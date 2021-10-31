import requests
import json
import logging

def cert_config():

    print('Loading the certificate configuration..\n')
    with open('config') as conf:
       config =json.load(conf)
    return config

def get_jira_tickets(config):

 print("Starting to fetch open tickets from queue...\n")
 components = ['Portfolio-Access', 'Agent-Access', 'Structure-Plugin-Access']

 for components in components:
      jql = "project+%3D+JIRASUP+AND+component+%3D+{0}" \
            "&maxResults=1000&?&fields=id,key,status,reporter".format(components)
      print ('Starting {0}'.format(components))
      logging.info('Starting {0}'.format(components))
      host =config['api']['host']+'search?jql='+ jql
      response = requests.get(host,verify=config['cert']['ca'],
                            cert=(config['cert']['crt'],config['cert']['key']))
      if response.status_code ==200 and response.json()['total'] > 0:
        logging.info("JSON Response {0}: "
                     "{1} Jira tickets with access request found."
                     "Starting to fetch userlist,ticket details".format(response.status_code,response.json()['total']))
        print("JSON Response {0}."
              "{1} Jira tickets with access request found."
              "Starting to fetch userlist , ticket details\n".format(response.status_code,response.json()['total']))
        for issue in response.json()['issues']:
            issue_keys = issue['key']
            print(issue_keys)
            logging.info('Jira ticket ID :'.format(issue_keys))
            user_list = issue['fields']['reporter']['name']
            print(user_list)
            logging.info('Requested User id '.format(user_list))
            post_users_group(issue_keys,user_list,config,components)
      elif response.status_code ==200 and response.json()['total'] == 0:
        logging.info("JSON Response {} :"
                     "But no JIRA ticket with access request found.".format(response.status_code))
        logging.info('Aboring the automation.')
        print("JSON Response is success."
              "But no JIRA ticket with access request found.\n\nAboring the automation..\n")

      elif response.status_code == 403:
        logging.error("Response {} :"
                      "Access to Jira api url is forbidden.".format(response.status_code))
        logging.error("Aboring the automation..")
        print("Response {} :Access to Jira api url is forbidden."
              "\n\nAboring the automation..".format(response.status_code))

      elif response.status_code == 500:
        logging.error("Response {} :"
                      "Can't proceed due to internal server error .".format(response.status_code))
        logging.error("Aboring the automation..")
        print("Response {} :"
              "Can't proceed due to internal server error.\n\nAboring the automation..".format(response.status_code))

      elif response.status_code == 400:
        logging.error("Response {0} :Can't find response."
                      "Might be problem with jql {1}.".format(response.status_code,config['api']['jql']))
        logging.error("Aboring the automation..")
        print("Response {0} :Can't find response."
              "Might be problem with jql {1}."
              "\n\nAboring the automation..\n".format(response.status_code,config['api']['jql']))

      elif response.status_code == 404:
        logging.error("Response {0} : Can't get the response. "
                      "Might be url {1} is wrong.".format(response.status_code,host))
        logging.error("Aboring the automation..")
        print("Response {0} : Can't get the response."
              "Might be url {1} is wrong."
              "\n\nAboring the automation..\n".format(response.status_code,host))

      else:
        logging.error("Api call failed due to {}".format(response.status_code))
        print("Api call failed due to {}".format(response.status_code))


def post_users_group(issue_keys,user_list,config,component):

    host = config['api']['host']+'group/user?groupname='+ config['api']['{0}'.format(component)]
    print(host)
    logging.info("JIRA API endpoint for ref {0}:".format(host))
    logging.info("Starting to add qualified users in {0} access.".format(component))
    print("Starting to add qualified users in {0} access.".format(component))
    payload = json.dumps({'name': user_list})
    response = requests.post(host,headers=config['myheaders'],
                             data=payload,verify=config['cert']['ca'],
                             cert=(config['cert']['crt'],config['cert']['key']))
    logging.info("JSON Response of user add request : {}".format(response.status_code))
    if response.status_code == 400 and  "already a member of " in response.text:
            logging.warning("JSON Response : {0}."
                            "User {1} is already part of the group".format(response.status_code,user_list))
            logging.info("Started commenting in ticket {}".format(user_list))
            print("User {} : is already part of the group\n".format(user_list))
            print("Started commenting in ticket {}\n".format(issue_keys))
            payload = json.dumps({"body": "User {0} is already have {1} ".format(user_list,component)})
            comment_issue(config,issue_keys,payload)
    elif response.status_code == 201:
            logging.info("Response {} : User {} added the group successfully".format(response.status_code,user_list))
            logging.info("Started commeting in {}".format(issue_keys))
            print("User {} added to the group".format(user_list))
            print("Started commeting in {}\n".format(issue_keys))
            payload = json.dumps({"body": "{0} Access provided for user {1}.".format(component,user_list)})
            comment_issue(config,issue_keys, payload)
    elif response.status_code == 404:
            logging.error("JSON response {}:"
                          "Requested group was not found or requested user was not found.".format(response.status_code))
            print("Requested group was not found or requested user was not found\n\n")
    elif response.status_code == 403:
            logging.error(("Response {}."
                           "Current user does not have administrator permissions.".format(response.status_code)))
            print("Current user does not have system administrator permissions\n\n")
    else:
            logging.error("Requested may not be sucessfulle due to http response {}".format(response.status_code))
            print("Requested may not be sucessfull due to http response {}\n\n".format(response.status_code))


def comment_issue(cert,issue_key,payload):

    host = cert['api']['host']+'issue/{}/comment'.format(issue_key)

    response = requests.post(host,headers=cert['myheaders'],
                             data=payload,verify=cert['cert']['ca'],
                             cert=(cert['cert']['crt'],cert['cert']['key']))

    if response.status_code == 201:
      print("Successfully commented in ticket {}\n".format(issue_key))
      logging.info("Successfully commented in ticket {}".format(issue_key))
    elif response.status_code == 403:
      logging.error("Rasponse {}. "
                    "Access forbidden to the url "
                    "for user trying to comment in ticket".format(response.status_code))
      print("Access forbidden to url "
            "for user trying to comment in ticket\n")
    elif response.status_code == 400:
      logging.error("Response {0}.Not able to comment in {1}."
                    "Either due to missing required fields,"
                    "invalid values or "
                    "user doesn't have add comment permission in the project.".format(response.status_code,issue_key))
      print("Not able to comment in {}."
            "Either due to missing required fields,"
            "invalid values or user doesn't have "
            "add comment permission in the project...\n".format(issue_key))
    else:
        logging.error("Not able to comment in {0} due to {1}".format(issue_key,response.status_code))
        print("Not able to comment in {0} due to {1}".format(issue_key,response.status_code))


def main():

    logging.basicConfig(filename='jira_automation.log',filemode='w', level=logging.DEBUG,
                        format='%(asctime)s -  %(levelname)s - %(message)s')
    print('Automation Start..\n')
    logging.info('Automation Start..')
    config =cert_config()
    get_jira_tickets(config)
    logging.info("Automation End.")
    print("Automation End..\n\n")

if __name__ == "__main__":
    main()



