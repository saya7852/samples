from cs50 import SQL
# assemble maxW table with sID & its most difficult wordID for each

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wordlist1.db")

# creating maxW if the table doesn’t exist
db.execute("CREATE TABLE IF NOT EXISTS maxW (s_ID INTEGER, v_ID INTEGER, FOREIGN KEY (v_ID) REFERENCES vWords (vID))")

# run a query to extract data from eLevelW1 & find THE HARDEST WORD within each sentence
h = db.execute("SELECT senID, elemID, vWordID, MIN(dLevel) FROM eLevelW1 GROUP BY senID")

# iterate over the query result and record vID (the wordID of the hardest) and sID (sentence ID)
for rows in h:
    vID = rows['vWordID']
    sID = rows['senID']

    # record both vID and sID in ‘maxW’
    db.execute("INSERT INTO maxW (v_ID, s_ID) VALUES (?, ?)", vID, sID)
