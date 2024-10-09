import json
from dataclasses import dataclass, field
from typing import Set
from pathlib import Path

from .manual_structure import XrefTarget

def require_validation(method):
    def decorator(self, *args, **kwargs):
        if not self._xref_targets:
            raise ValueError("_xref_targets must be populated before calling this method. Did you run Redirects.validate()?")
        return method(self, *args, **kwargs)
    return decorator

@dataclass
class Redirects:
    _raw_redirects: dict[str, list[str]]
    _redirects_script: str

    _xref_targets: dict[str, XrefTarget] = field(default_factory=dict)

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

        initial_identifiers_without_redirects = xref_targets.keys() - self._raw_redirects.keys()
        orphan_identifiers_not_in_source = self._raw_redirects.keys() - xref_targets.keys()

        if orphan_identifiers_not_in_source:
            raise RuntimeError(f"following identifiers missing in source: {orphan_identifiers_not_in_source}")

        identifiers_without_redirects = set()
        for input_identifier in initial_identifiers_without_redirects:
            found = False
            for output_identifier, locations in self._raw_redirects.items():
                if input_identifier in map(lambda loc: loc.split('#')[-1], locations[1:]):
                    found = True
                    break
            if not found:
                identifiers_without_redirects.add(input_identifier)
        if len(identifiers_without_redirects) > 0:
            raise RuntimeError(f"following identifiers don't have a redirect: {identifiers_without_redirects}")

        client_side_redirects = {}
        server_side_redirects = {}
        divergent_redirects = set()
        redirect_anchors = set()
        for identifier, locations in self._raw_redirects.items():
            if locations[0] != xref_targets[identifier].path:
                raise RuntimeError(f"the first location of '{identifier}' must be its current output path")

            for location in locations[1:]:
                if '#' in location:
                    if location not in client_side_redirects:
                        client_side_redirects[location] = f"{xref_targets[identifier].path}#{identifier}"
                    else:
                        divergent_redirects.add(location)
                    redirect_anchors.add(location.split('#')[1])
                else:
                    if location not in server_side_redirects:
                        server_side_redirects[location] = xref_targets[identifier].path
                    else:
                        divergent_redirects.add(location)
        if len(divergent_redirects) > 0:
            raise RuntimeError(f"following paths redirect to different locations: {divergent_redirects}")
        if conflicting_anchors := set([anchor for anchor in redirect_anchors if anchor in self._raw_redirects.keys()]):
            raise RuntimeError(f"following anchors found that conflict with identifiers: {conflicting_anchors}")

        transitive_redirects = {}
        for server_from, server_to in server_side_redirects.items():
            for client_from, client_to in client_side_redirects.items():
                path, anchor = client_from.split('#')
                if server_from == path:
                    transitive_redirects[client_from] = f"{server_to}#{anchor}"
        if len(transitive_redirects) > 0:
            modifications = "\n\t".join([f"{source} -> {dest}" for source, dest in transitive_redirects.items()])
            raise RuntimeError(f"following paths have server-side redirects, please modify them to represent their final paths:\n\t{modifications}")

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
                client_redirects[anchor] = f"{self._xref_targets[identifier].path}#{identifier}"

        return self._redirects_script.replace('REDIRECTS_PLACEHOLDER', json.dumps(client_redirects))
