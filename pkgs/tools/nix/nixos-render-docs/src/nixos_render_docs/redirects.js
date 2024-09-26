// the following code matches the current page's anchor against the set of redirects.
//
// it is written to minimize the latency between page load and redirect.
// therefore we avoid function calls, copying data, and unnecessary loops.

// anchor starts with the hash character (`#`),
// but our redirect declarations don't, so we strip it.
// example:
//     document.location.hash -> '#foo'
//     document.location.hash.substring(1) -> 'foo'
const anchor = document.location.hash.substring(1);

const redirects = REDIRECTS_PLACEHOLDER;
if (redirects[anchor]) document.location.href = redirects[anchor];
