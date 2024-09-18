// the following code matches the current page's URL against the set of redirects.
//
// it is written to minimize the latency between page load and redirect.
// therefore we avoid function calls, copying data, and unnecessary loops.
// IMPORTANT: we use stateful array operations and their order matters!
//
// matching URLs is more involved than it should be:
//
// 1. `document.location.pathname` can have an arbitrary prefix.
//
// 2. `path_to_root` is set by mdBook. it consists only of `../`s and
//    determines the depth of `<path>` relative to the prefix:
//
//          `document.location.pathname`
//        |------------------------------|
//        /<prefix>/<path>/[<file>[.html]][#<anchor>]
//                  |----|
//              `path_to_root` has same number of path segments
//
//    source: https://phaiax.github.io/mdBook/format/theme/index-hbs.html#data
//
// 3. the following paths are equivalent:
//
//        /foo/bar/
//        /foo/bar/index.html
//        /foo/bar/index
//
//  4. the following paths are also equivalent:
//
//        /foo/bar/baz
//        /foo/bar/baz.html
//

let segments = document.location.pathname.split('/');

// normalize file name
let file = segments.pop();
if (file === '') {
  file = 'index.html';
} else if (!file.endsWith('.html')) {
  file = file + '.html';
}

// anchor starts with the hash character (`#`),
// but our redirect declarations don't, so we strip it.
// example:
//     document.location.hash -> '#foo'
//     document.location.hash.substring(1) -> 'foo'
const anchor = document.location.hash.substring(1);

const redirects = REDIRECTS_JSON_PLACEHOLDER;
if (redirects[`${file}#${anchor}`]) {
  document.location.href = redirects[`${file}#${anchor}`];
}
