import pandas as pd
import time
import datetime
import smtplib
import io
import pytz
import requests

from src.yfi_gainers_losers_scraper import get_day_gainers, get_day_losers, get_stock_info, prepare_df
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from slack import WebClient
from slack.errors import SlackApiError

def export_csv(df):
    with io.StringIO() as buffer:
        df.to_csv(buffer, index=False)
        return buffer.getvalue()


# def export_xls(df):
#     with io.BytesIO() as buffer:
#         writer = pd.ExcelWriter(buffer)
#         df.to_excel(writer, index=False)
#         writer.save()
#         return buffer.getvalue()


def send_dataframe(username, password, send_to, to_address, send_from, exporters, subject, body, df):
    multipart = MIMEMultipart()
    multipart['From'] = send_from
    multipart['To'] = send_to
    multipart['Subject'] = subject

    for filename in exporters:
        attachment = MIMEApplication(exporters[filename](df))
        attachment['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        multipart.attach(attachment)
    multipart.attach(MIMEText(body, 'html'))
    s = smtplib.SMTP("smtp.gmail.com:587")
    s.starttls()
    s.login(username, password)
    s.sendmail(send_from, to_address, multipart.as_string())
    s.quit()


def part_of_day():
    current_time = datetime.datetime.now(pytz.timezone('EST'))
    if current_time.hour < 12:
        return 'morning'
    else:
        return 'afternoon'


# def main():
#     StartTime = time.time()
#
#     #######################################
#     ###                                 ###
#     ###   Scrape top gainers & losers   ###
#     ###                                 ###
#     #######################################
#
#     # get biggest gainers (set no n if you want all gainers)
#     # day_gainers = get_day_gainers(n=3)
#     # get worst performers (set no n if you want all losers)
#     n=5
#     day_losers = get_day_losers(n)
#
#     #############################################
#     ###                                       ###
#     ###   Scrape Other Important Stock Info   ###
#     ###                                       ###
#     #############################################
#
#     Symbols_losers = day_losers['Symbol'].to_list()
#     # Symbols_gainers = day_gainers['Symbol'].to_list()
#
#     losers_financial_info = get_stock_info(Symbols_losers)
#     # gainers_financial_info = get_stock_info(Symbols_gainers)
#
#     day_losers = prepare_df(day_losers, losers_financial_info)
#     # day_gainers = pd.merge(day_gainers, gainers_financial_info, on='Symbol', how="left")
#
#     #######################################
#     ###                                 ###
#     ###   Send e-mail to mailing list   ###
#     ###                                 ###
#     #######################################
#
#     current_time = datetime.datetime.now(pytz.timezone('EST'))
#
#     print('• Sending e-mail')
#
#     username = "propelpyltd"
#     password = "pptwlocwooxfjtri"
#     send_from = 'propelpyltd@gmail.com'
#     send_to = 'propelpyltd@gmail.com'
#     bcc = ['jr599@cornell.edu'] #'jefflapaix@gmail.com'
#     to_address = [send_to] + bcc
#
#     exporters = {'TopLosers.csv': export_csv}
#     subject = "Top losers this " + current_time.strftime('%A') + " " + part_of_day()
#     body = """
#     Good """ + part_of_day() + """,<br>
#     <br>
#     See the workbook attached for the top """ + str(n) + """ losers as of """ + current_time.strftime("%I:%M %p") + """ EST.<br>
#     <br>
#     Happy trading!<br>
#     June's Bot 🤖
#     """
#
#     df = day_losers
#
#     send_dataframe(username, password, send_to, to_address, send_from, exporters, subject, body, df)
#
#     #############################################
#     ###                                       ###
#     ###   Calculate time script took to run   ###
#     ###                                       ###
#     #############################################
#
#     ExecutionTime = (time.time() - StartTime)
#     minutes = ExecutionTime / 60
#     minutes_trunc = int(ExecutionTime / 60)
#     seconds = int(round((minutes - minutes_trunc) * 60, 0))
#
#     if ExecutionTime > 60:
#         print('Script is complete! This script took ' + format(str(minutes_trunc)) + ' minute(s) and ' + format(
#             str(seconds)) + ' second(s) to run.')
#     else:
#         print('Script is complete! This script took ' + format(str(round(ExecutionTime, 0))) + ' seconds to run.')

def main():
    StartTime = time.time()

    #######################################
    ###                                 ###
    ###   Scrape top gainers & losers   ###
    ###                                 ###
    #######################################

    # get biggest gainers (set no n if you want all gainers)
    # day_gainers = get_day_gainers(n=3)
    # get worst performers (set no n if you want all losers)
    n=20
    day_losers = get_day_losers(n)

    #############################################
    ###                                       ###
    ###   Scrape Other Important Stock Info   ###
    ###                                       ###
    #############################################

    Symbols_losers = day_losers['Symbol'].to_list()
    # Symbols_gainers = day_gainers['Symbol'].to_list()

    losers_financial_info = get_stock_info(Symbols_losers)
    # gainers_financial_info = get_stock_info(Symbols_gainers)

    day_losers = prepare_df(day_losers, losers_financial_info)
    # day_gainers = pd.merge(day_gainers, gainers_financial_info, on='Symbol', how="left")

    #########################################
    ###                                   ###
    ###   Send Slack message to channel   ###
    ###                                   ###
    #########################################

    current_time = datetime.datetime.now(pytz.timezone('EST'))
    print('• Sending message')

    # Authenticate to the Slack API via the generated token
    client = WebClient("<YOUR SLACK OAUTH TOKEN HERE>")

    # TODO: left off at trying to figure out how to send the df as a png image in the Slack App as shown in test.ipynb saved on the desktop

    # Send csv file
    client.files_upload(
                        channels="<YOUR SLACK CHANNEL'S ID HERE>",
                        initial_comment="""
                        Good """ + part_of_day() + """,\n\nSee the workbook attached for the top """ + str(n) + """ losers as of """ + current_time.strftime("%I:%M %p") + """ EST.\n\nHappy trading!\nJune's Bot 🤖
                        """,
                        filename="TopLosers.csv",
                        content=export_csv(day_losers)
                        )

    #############################################
    ###                                       ###
    ###   Calculate time script took to run   ###
    ###                                       ###
    #############################################

    ExecutionTime = (time.time() - StartTime)
    minutes = ExecutionTime / 60
    minutes_trunc = int(ExecutionTime / 60)
    seconds = int(round((minutes - minutes_trunc) * 60, 0))

    if ExecutionTime > 60:
        print('Script is complete! This script took ' + format(str(minutes_trunc)) + ' minute(s) and ' + format(
            str(seconds)) + ' second(s) to run.')
    else:
        print('Script is complete! This script took ' + format(str(round(ExecutionTime, 0))) + ' seconds to run.')

if __name__ == "__main__":
    main()