import os


# CYBER ESCAPE PARTICIPANTS
os.chdir(r"C:\Users\Zjaffen1\Desktop\CSAM data")

fileHandle = open(r'escape_participants.csv', 'r')

for line in fileHandle:
    fields = line.split('|')

    print(len(fields)) # prints the first fields value

fileHandle.close()

# TRACKS UNIQUE EMAILS
emails = []
total = 0

for email in fields:
    if email.lower() not in emails and 'test' not in email.lower():
        emails.append(email)
    if 'test' not in email.lower():
        total += 1

print(len(emails))


# SP REGISTRANTS
# os.chdir(r"C:\Users\Zjaffen1\Desktop\CSAM data")
# SP_data = pd.read_csv(r'SP_registration.csv')

# print(SP_data.head())