READ ME

To test this skill in your own environment, edit lines 6 and 7 in the vmax_requests file to reflect your own server details.
Please note that this app in configured for Unisphere 8.4 only.

For setup details, please see https://developer.amazon.com/blogs/post/Tx14R0IYYGH3SKT/Flask-Ask-A-New-Python-Framework-for-Rapid-Alexa-Skills-Kit-Development . 
Follow the steps, but substitute the VMAX files and template for the memory_game files, and enter the following for the intent schema and sample utterances:

- Intent Schema:

{
  "intents": [
    {
      "intent": "YesIntent"
    },
    {
      "intent": "ChooseArrayIntent",
      "slots": [
        {
          "name": "index",
          "type": "AMAZON.NUMBER"
        }
      ]
    },
    {
      "intent": "ListAlertsIntent"
    },
    {
      "intent": "GoodbyeIntent"
    }
  ]
}

- Sample Utterances:

YesIntent yes

YesIntent sure

ChooseArrayIntent {index}

ListAlertsIntent alerts

ListAlertsIntent alert

GoodbyeIntent no

GoodbyeIntent goodbye

GoodbyeIntent bye

Try the following sequence to test the app:

You - "Alexa, start array alerts"
Alexa - "Welcome to VMAX Alexa. I am going to list out the arrays in your environment. Ready?"
You - "Yes"
Alexa - "There are two VMAX arrays in your environment. These are 0: '000197800128', 1: '000296800647'.
       Select an array by stating its corresponding position in the list.
       Which array would you like to query?"
You - "Zero"
Alexa - "The details of the selected alerts are as follows: 0. Alert description is (blah blah). The alert was created on (blah blah). 
         1. Alert description is (blah blah). The alert was created on (blah blah). Would you like to choose another array?"
You - "No"
Alexa - "Goodbye and thank you."
