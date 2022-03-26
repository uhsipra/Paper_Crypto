# Paper Crypto
#### Video Demo:  https://youtu.be/BLSAk1-_JMc
#### Description: I decided to make a paper trading web application for cryptocurrency.

#### My paper crypto web application was built with flask, python, bootstrap, and sqlite3.

 The idea for this project came to me from the "finance" assignment we did for week 9. I thought it would be cool and 
 helpful for users who are interested in the rising popularity of cryptocurrency and wanted to test it via paper trading
 before using real money. Paper trading is the same as regular trading with the one condition that all the "funds" that are
 used are not real money, but instead fake practise money.
 The application allows users to register for an account by entering a username and password, if the username is available then the 
 account will be made. 
 If a user wants to change their password, there is a "reset password" tab that allows for just that. The user will be asked
 to input their old password and the new password they would like, if the new password is the same as the old password the application
 will alert the user of this and allow them to enter a different password.

 I used the lunarcrush opensource API to get real time information on cryptocurrency prices, names, and news articles.
 In order to run the entire program, a user will need to signup on lunarcrush to get a free API key which will allow users
 to access the lunarsource API information.

 The webapp also has error checking for when users are logging in, will tell and redirect users if login information is incorrect.
 Will also tell users if registration information is already taken, if it isnt possible to buy/sell a crypto and the reason why.

 The web app lets users register for an account and automatically start off with 10,000$ of paper money to trade, similar.
 The web app has features such as searching up quotes, buying, selling, and looking up news articles on specific cryptocurrencies.
 The news tab lets users enter a cryptocurrency ticker and will return 10 current news articles on that specific cryptocurrency.
 The articles shown also have a hyperlink that users can click which will direct users to the website of the article source.
 The history tab shows users the transaction history from 1, 3, and 6 months ago. The table shows the name of the cryptocurrency,
 the amount of shares transacted, the total price of the transaction, if the transaction was a BUY or SELL, and the date and time
 of the transaction.

 Application.py contains the main code for the webapp.
 Crypto.db is the database file that stores all the tables used via SQLite3.
 The templates file includes all the html files created for the webapp.
 The static file includes the styles.css file which contains any styling alterations.
