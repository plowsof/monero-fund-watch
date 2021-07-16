3 problems i've noticed:

1. The viewkey for the Monero general fund is public, however, there are several steps involved with creating a view-only wallet and you can't just link someone to look at it (especially someone not involved with Monero).
2. People who do create a view-only wallet will be confused by false inputs which are actually 'change' outputs from an outgoing transaction (which are disclosed on Moneros gitlab repository by @binaryFate.
3. There was some unrest over 2020-2021 transparency report being 'late'.

My proposed solutions:

1. Tweet every donation that is received so people can simply visit the twitter account and scroll through its activity.
2. Donation tweets will be delayed for 1 hour. This will give @binaryFate enough time to disclose any outgoing transactions on gitlab. If the input is found to be a change output - instead of tweeting the amount - binaryFates comment will be directly uploaded instead e.g. "Donating ?xmr to (some proposal) : (proposal link)."
3. Because updates will be posted live, there will be less / no unrest for the yearly transparency report as updates will happen in near real time.

How i've solved this:

- use tx-notify from monero-wallet-rpc to run a python script when incoming transactions are received.
- use a webscraper to check binaryFates recent activity on gitlab.
- send the tweet.
  
Problems:

Contributions to ccs proposals are not the only outgoing transactions from the general fund (which cause the false change inputs) so for this script to validate all inputs - these payments need to be disclosed also e.g. "Withdrawing ?xmr from the general fund to purchase server bandwidth."

The webscraping method is a 'hack'. Outgoing transactions should ideally be disclosed in a simple text file somewhere that a script can easily parse
