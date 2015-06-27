nfs:
  server:
    exports: 
      /srv/home: "*(rw,sync,no_subtree_check)"
  mount:
    somename:
      mountpoint: "/some/path"
      location: "hostname:/path"
      opts: "vers=3,rsize=65535,wsize=65535"
      persist: True
      mkmnt: True
  unmount:
    someothername:
      mountpoint: "/some/other/path"
      location: "hostname:/other/path"
      persist: False

