import streamlit_authenticator as stauth

# Define your passwords in plain text
passwords = ['your_password1', 'your_password2']

# Generate hashed passwords
hashed_passwords = stauth.Hasher(['abc', 'def']).generate()

# Output the hashed passwords
print(hashed_passwords)
