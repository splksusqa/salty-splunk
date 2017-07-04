# create site with grains data
# the content under site1 or site2 could be either
# 1. dict, with minion name as key
# 2. list, runner will auto assign the minion to these grain datas

#ex.
#sites:
#  site1:
#    minion_name:
#        - - search-head
#          - search-head-cluster-member
#  site2:
#      - - search-head
#        - search-head-cluster-member
#        - search-head-cluster-first-captain
	   - -
#        - indexer