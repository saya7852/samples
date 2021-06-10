from cs50 import SQL

# this is a program to test the queries

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wordlist1.db")

h = db.execute("SELECT element, hElement FROM corpus2 WHERE elementID IN (SELECT eID FROM sentences WHERE sID IN (SELECT s_ID FROM maxW WHERE v_ID = (SELECT vID FROM vWords WHERE vWord = 'THEREFORE')))")

#if len(h) < 1:
    #responses.append('Sorry!  We could not find that word!')
    #return render_template("generate.html", responses=responses)

ph = []
count = 0
for i in h:

    if count < 4:
        word = i["element"]
        if word != "SSSSS":
            word = ' ' + i["element"]
        else:
            if i["hElement"] != None:
                word = i["hElement"]
            else:
                word = ' '
                count += 1


        ph.append(word)
        separator = ''
        phrase = separator.join(ph)

print(phrase)
