from beem import Hive
from beem.exceptions import MissingKeyError

hiveUsername = input("Hive username: ")
hiveWalletPassword = input("Wallet password: ")

hive = Hive()

hive.wallet.unlock(hiveWalletPassword)
if not hive.wallet.unlocked():
    hive.wallet.create(hiveWalletPassword)
    print('Wallet created.')
else:
    print('Wallet unlocked.')

try:
    hive.wallet.getPostingKeyForAccount(hiveUsername)
    print('Key already exist for @{user}'.format(user=hiveUsername))
except MissingKeyError:
    hivePostingKey = input("Posting key: ")
    hive.wallet.addPrivateKey(hivePostingKey)
    print('Key added.')



