import json
from dataclasses import dataclass, field
from typing import Set
from pathlib import Path

from .manual_structure import XrefTarget

def require_validation(method):
    def decorator(self, *args, **kwargs):
        if self._is_invalid:
            raise ValueError("Validation failed. Run Redirects.validate() and check report_validity() for details.")
        if not self._xref_targets:
            raise ValueError("_xref_targets must be populated before calling this method. Did you run Redirects.validate()?")
        return method(self, *args, **kwargs)
    return decorator

@dataclass
class Redirects:
    _raw_redirects: dict[str, list[str]]
    _redirects_script: str

    _xref_targets: dict[str, XrefTarget] = field(default_factory=dict)
    orphan_identifiers: set = field(default_factory=set)
    identifiers_without_redirects: set = field(default_factory=set)
    identifiers_missing_current_outpath: set = field(default_factory=set)
    divergent_redirects: set = field(default_factory=set)
    conflicting_anchors: set = field(default_factory=set)
    transitive_redirects: dict[str, str] = field(default_factory=dict)

    def validate(self, xref_targets):
        """
        Parse redirects from an static set of identifier-locations pairs

        - Ensure semantic correctness of the set of redirects
          - Identifiers not having a redirect entry
          - Orphan identifiers not present in source
          - Paths redirecting to different locations
          - Identifiers conflicting with redirect entries
          - Client-side redirects to paths having a server-side redirect (transitivity)
        - Flatten redirects into simple key-value pairs for simpler indexing
        - Segregate client and server side redirects
        """
        self._xref_targets = xref_targets
        redirection_targets = {target.path for target in xref_targets.values()}

        self.identifiers_without_redirects = xref_targets.keys() - self._raw_redirects.keys()
        self.orphan_identifiers = self._raw_redirects.keys() - xref_targets.keys()

        client_side_redirects = {}
        server_side_redirects = {}
        all_client_locations = set()

        for identifier, locations in self._raw_redirects.items():
            if identifier not in xref_targets:
                continue

            if locations[0] != xref_targets[identifier].path:
                self.identifiers_missing_current_outpath.add(identifier)

            for location in locations[1:]:
                if '#' in location:
                    path, anchor = location.split('#')

                    if location in all_client_locations:
                        self.conflicting_anchors.add(location)
                    else:
                        all_client_locations.add(location)

                    if anchor in self.identifiers_without_redirects:
                        self.identifiers_without_redirects.remove(anchor)

                    if location not in client_side_redirects:
                        client_side_redirects[location] = f"{xref_targets[identifier].path}#{identifier}"
                    else:
                        self.divergent_redirects.add(location)
                else:
                    if location not in server_side_redirects:
                        server_side_redirects[location] = xref_targets[identifier].path
                    else:
                        self.divergent_redirects.add(location)

        for target in {location.split('#')[0] for location in all_client_locations}:
            identifiers = [identifier for identifier, xref in xref_targets.items() if xref.path == target]
            anchors = {location.split('#')[1] for location in all_client_locations}
            self.conflicting_anchors.update(anchors.intersection(identifiers))

        for server_from, server_to in server_side_redirects.items():
            for client_from, client_to in client_side_redirects.items():
                path, anchor = client_from.split('#')
                if server_from == path:
                    self.transitive_redirects[client_from] = f"{server_to}#{anchor}"

        if self._is_invalid():
            raise InvalidRedirects(self)

    class InvalidRedirects(Exception):
        def __str__(self) -> str:
            # TODO: figure out passing the error analysis
            errors = []
            if self.orphan_identifiers:
                errors.append(f"Following identifiers missing in source: {self.orphan_identifiers}")
            if self.identifiers_without_redirects:
                errors.append(f"Following identifiers don't have a redirect: {self.identifiers_without_redirects}")
            if self.identifiers_missing_current_outpath:
                errors.append(f"Following identifiers don't have their current out path set or is invalid: {self.identifiers_missing_current_outpath}")
            if self.divergent_redirects:
                errors.append(f"Following paths redirect to different locations: {self.divergent_redirects}")
            if self.conflicting_anchors:
                errors.append(f"Following anchors found that conflict with identifiers: {self.conflicting_anchors}")
            if self.transitive_redirects:
                modifications = "\n\t".join([f"{source} -> {dest}" for source, dest in self.transitive_redirects.items()])
                errors.append(f"Following paths have server-side redirects, please modify them to represent their final paths:\n\t{modifications}")
            return "\n".join(errors)

    @property
    def _is_invalid(self) -> bool:
        return bool(self.__str__())

    @require_validation
    def get_client_redirects(self, redirection_target: str):
        client_redirects = {}
        for identifier, locations in self._raw_redirects.items():
            for location in locations[1:]:
                if '#' not in location:
                    continue
                path, anchor = location.split('#')
                if path != redirection_target:
                    continue
                client_redirects[anchor] = location

        return self._redirects_script.replace('REDIRECTS_PLACEHOLDER', json.dumps(client_redirects))
