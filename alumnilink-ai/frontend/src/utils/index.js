export function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function truncate(str, n = 100) {
  return str && str.length > n ? str.slice(0, n) + "..." : str;
}
