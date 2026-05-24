# Historical note only. Do not apply this patch as part of the current baseline.
#
# It was used to suppress a real SSPI/CPU configuration consistency check in a
# local apycula install. That made the build continue, but also made target
# metadata mistakes harder to distinguish from tool limitations.
#
# Keep upstream gowin_pack.py while re-establishing a clean Tang Primer 25K
# baseline. If the clean flow still fails, capture the exact upstream error
# before considering any local patch again.
