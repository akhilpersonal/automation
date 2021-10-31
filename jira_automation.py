import requests
import json
import logging
import sys

def cert_config():
    print('Loading the certificate configuration..\n')
    with open('config') as conf:
       config =json.load(conf)
    return config

def get_jira_tickets(config):
    #config =cert_config()
    print('Starting  to fetch open tickets from queue...\n')
    host =config['api']['host']+'search?jql='+ config['api']['jql']
    response = requests.get(host,verify=config['cert']['ca'],cert=(config['cert']['crt'],config['cert']['key']))
    #print("JSON Response Status Code : {}".format(response.status_code))
    user_key_dic = {}
    if response.status_code ==200 and response.json()['total'] > 0:
        logging.info("JSON Response {}:Jira tickets with access request found.Starting to fetch userlist,ticket details".format(response.status_code))
        print("JSON Response {} Jira tickets with access request found.Starting to fetch userlist,ticket details".format(response.status_code))
        #issue_count = response.json()['total'] - response.json()['startAt']
        #print("Total Jira Ticket : {}".format(issue_count))
        user_list = []
        issue_keys = []

        for issue in response.json()['issues']:
            issue_keys.append(issue['key'])
            user_list.append(issue['fields']['reporter']['name'])
            issue_count = len(user_list)
        #logging.info("List of Users:{}".format(user_list))
        #print("User List:{}".format(user_list))
        #logging.info("Corresponding Jira Issue Keys:{}".format(issue_keys))
        #print("Corresponding Jira Keys :{}".format(issue_keys))
        logging.info("Total qualified tickets found :{}".format(issue_count))
        print("Total qualified tickets :{}".format(issue_count))
        user_key_dic['username'] = user_list
        user_key_dic['IssueKey'] = issue_keys
        print("Qualified tickets and user details - {}\n".format(user_key_dic))
        logging.info("Qualified tickets and user details - {}".format(user_key_dic))
        return user_key_dic
    elif response.status_code ==200 and response.json()['total'] == 0:
        logging.info("JSON Response {} : But no JIRA ticket with access request found.".format(response.status_code))
        logging.info('Aboring the automation.')
        print("JSON Response is success.But no JIRA ticket with access request found.\n\nAboring the automation..\n")
        #sys.exit(0)
    elif response.status_code == 403:
        logging.error("Response {} :Access to Jira api url is forbidden.".format(response.status_code))
        logging.error("Aboring the automation..")
        print("Response {} :Access to Jira api url is forbidden.\n\nAboring the automation..".format(response.status_code))
        sys.exit(1)
    elif response.status_code == 500:
        logging.error("Response {} :Can't proceed due to internal server error .".format(response.status_code))
        logging.error("Aboring the automation..")
        print("Response {} :Can't proceed due to internal server error.\n\nAboring the automation..".format(response.status_code))
        sys.exit(1)
    elif response.status_code == 400:
        logging.error("Response {0} :Can't find response. Might be problem with jql {1}.".format(response.status_code,config['api']['jql']))
        logging.error("Aboring the automation..")
        print("Response {0} :Can't find response. Might be problem with jql {1}.\n\nAboring the automation..\n".format(response.status_code,config['api']['jql']))
        #sys.exit(1)
    elif response.status_code == 404:
        logging.error("Response {0} : Can't get the response. Might be url {1} is wrong.".format(response.status_code,host))
        logging.error("Aboring the automation..")
        print("Response {0} : Can't get the response. Might be url {1} is wrong.\n\nAboring the automation..\n".format(response.status_code,host))
        #sys.exit(1)
    else:
        logging.error("Api call failed due to {}".format(response.status_code))
        print("Api call failed due to {}".format(response.status_code))
        #sys.exit("Unknown Error")
    #print("Qualified tickets and user details - {}\n".format(user_key_dic))


def post_users_group(user_key_dic,config):


    host = config['api']['host']+'group/user?groupname='+ config['api']['group']
    logging.info("Started to add qualified users in portfolio create user permission group.")
    print("Started to add qualified users in portfolio create user permission group.\n")

    for i in range(len(user_key_dic['IssueKey'])):
        payload = json.dumps({'name': user_key_dic['username'][i]})
        #print(i)
        response = requests.post(host,headers=config['myheaders'],data=payload,verify=config['cert']['ca'],cert=(config['cert']['crt'],config['cert']['key']))
        #print(response.status_code)
        logging.info("JSON Response of user add request : {}".format(response.status_code))
        #print(response.text)
        #print(type(response.text))
        if response.status_code == 400 and  "already a member of " in response.text:
            logging.warning("JSON Response : {0}.User {1} is already part of the group".format(response.status_code,user_key_dic['username'][i]))
            logging.warning("Started commenting in ticket {}".format(user_key_dic['IssueKey'][i]))
            print("User {} : is already part of the group".format(user_key_dic['username'][i]))
            print("Started commenting in ticket {}\n".format(user_key_dic['IssueKey'][i]))
            payload = json.dumps({"body": "User {} is already have portfolio create plan access.You will be able to create Portfolio from https://jira-staging.akamai.com/jira/secure/PortfolioCreate.jspa".format(user_key_dic['username'][i])})
            comment_issue(config,user_key_dic['IssueKey'][i],payload)
        elif response.status_code == 201:
            logging.info("Response {} : User {} added the group successfully".format(response.status_code,user_key_dic['username'][i]))
            logging.info("Started commeting in {}".format(user_key_dic['IssueKey'][i]))
            print("User {} added to the group".format(user_key_dic['username'][i]))
            print("Started commeting in {}\n".format(user_key_dic['IssueKey'][i]))
            payload = json.dumps({"body": "Portfolio create permission provided. You will be able to create Portfolio from https://jira-staging.akamai.com/jira/secure/PortfolioCreate.jspa"})
            comment_issue(config,user_key_dic['IssueKey'][i], payload)
        elif response.status_code == 404:
            logging.error("JSON response {}:Requested group was not found or requested user was not found.".format(response.status_code))
            print("Requested group was not found or requested user was not found\n\n")
        elif response.status_code == 403:
            logging.error(("Response {}.Current user does not have administrator permissions.".format(response.status_code)))
            print("Current user does not have system administrator permissions\n\n")
        else:
            logging.error("Requested may not be sucessfulle due to http response {}".format(response.status_code))
            print("Requested may not be sucessfull due to http response {}\n\n".format(response.status_code))


def comment_issue(cert,issue_key,payload):
    #post_users_group()
    #cert = cert_config()
    host = cert['api']['host']+'issue/{}/comment'.format(issue_key)
    #print(host)
      #payload = json.dumps({"body": "Portfolio create permission provided. You will be able to create Portfolio from https://jira-staging.akamai.com/jira/secure/CreateStructure.jspa"})
    response = requests.post(host,headers=cert['myheaders'],data=payload,verify=cert['cert']['ca'],cert=(cert['cert']['crt'],cert['cert']['key']))
    #print(response.status_code)
    if response.status_code == 201:
      print("Successfully commented in ticket {}\n".format(issue_key))
      logging.info("Successfully commented in ticket {}".format(issue_key))
    elif response.status_code == 403:
      logging.error("Rasponse {}. Access forbidden to the url for user trying to comment in ticket".format(response.status_code))
      print("Access forbidden to url for user trying to comment in ticket\n")
    elif response.status_code == 400:
      logging.error("Response {0}.Not able to comment in {1}.Either due to missing required fields,invalid values or user doesn't have add comment permission in the project.".format(response.status_code,issue_key))
      print("Not able to comment in {}.Either due to missing required fields,invalid values or user doesn't have add comment permission in the project...\n".format(issue_key))
    else:
        logging.error("Not able to comment in {0} due to {1}".format(issue_key,response.status_code))
        print("Not able to comment in {0} due to {1}".format(issue_key,response.status_code))


def main():

    logging.basicConfig(filename='jira_automation.log',filemode='w', level=logging.DEBUG,
                        format='%(asctime)s -  %(levelname)s - %(message)s')
    print('Automation Start..\n')
    logging.info('Automation Start..')
    config =cert_config()
    user_key_dic = get_jira_tickets(config)
    if user_key_dic:
        post_users_group(user_key_dic,config)
    logging.info("Automation End.")
    print("Automation End..\n\n")

if __name__ == "__main__":
    main()



