major = 13
hotfix = 0
hotfix_str = chr(ord('a') + hotfix) if hotfix else ''
beta = 1
beta_str = '-beta{}'.format(beta) if beta > 0 else ''
canary = True
release = 'r{}{}{}'.format(major, hotfix_str, beta_str)
