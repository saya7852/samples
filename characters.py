from cs50 import SQL

# this program updates 'corpus' table after .csv data is imported via temp. table

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wordlist1.db")

# update all special characters in 'element' column into "SSSSS" and add tag info to enable word searches
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'sSen', startEnd = 'start' WHERE element = '<S>'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'eTxt', startEnd = 'end' WHERE element = '<EOL>'")

# below specifying double quotes (") doesn't work...  trying to find a way to do it in .py
# db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'dQuo' WHERE element = '""'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'oPren' WHERE element = '('")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'cPren' WHERE element = ')'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'oCurl' WHERE element = '{'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'cCurl' WHERE element = '}'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'oSqua' WHERE element = '['")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'cSqua' WHERE element = ']'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'semCol' WHERE element = ';'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'colon' WHERE element = ':'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'exc' WHERE element = '!'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'ques' WHERE element = '?'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'slash' WHERE element = '/'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'equal' WHERE element = '='")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'plus' WHERE element = '+'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'comma' WHERE element = ','")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'period' WHERE element = '.'")
db.execute("UPDATE corpus SET element = 'SSSSS', tags = 'sQuote' WHERE element = ''''")


