from github.GithubException import GithubException, UnknownObjectException
from github.GithubObject import NotSet
from yaml import load, dump, scanner
import logging


def checkRepoExists(user, repo_name):
    repo = None
    try:
        repo = user.get_repo(repo_name)
        logging.debug("Repo {} exists".format(repo.name))
    except GithubException as ge:
        logging.warning("Unable to find Repo: status:{}, data:{}".
              format(ge.status, ge.data))

    return repo


def createRepo(user, repo):
    try:
        logging.info("Creating repo {}...".format(repo))
        repo = user.create_repo(repo, description="",
                                homepage=NotSet, private=False,
                                has_issues=True,
                                has_wiki=False, has_downloads=True,
                                auto_init=True,
                                gitignore_template=NotSet)

        logging.info("Created repo {}...".format(repo.name))
        return repo

    except GithubException as ge:
        logging.error("Unable to create repo {}...".format(repo))
        logging.debug("status:{}, data:{}".format(ge.status, ge.data))


def createIssueFromInstructions(agentid, repo, instructions):
    try:
        logging.debug(dump(instructions))

        issue_title = instructions["issue"]["title"]
        issue_body = instructions["issue"]["body"]
        issue_label = agentid

        issue = repo.create_issue(title=issue_title, body=dump(issue_body),
                                  labels=[issue_label])
        return issue
    except scanner.ScannerError as yse:
        logging.error("Scanner Error: {}".format(yse))


def createIssueFromFile(agentid, repo, reqfile):
    try:
        stream = open(reqfile, 'r')
        instructions = load(stream)
        stream.close()
        logging.debug(dump(instructions))

        issue_title = instructions["issue"]["title"]
        issue_body = instructions["issue"]["body"]

        logging.debug(type(dump(issue_body)))
        issue_label = agentid

        issue = repo.create_issue(title=issue_title, body=dump(issue_body),
                                  labels=[issue_label])
        return issue
    except IOError as ioe:
        logging.error("I/O Error: {}".format(ioe))
    except scanner.ScannerError as yse:
        logging.error("Scanner Error: {}".format(yse))


def getClosedIssueComments(repo, issue_number):
    comment_contents=[]
    try:
        issue = repo.get_issue(int(issue_number))
        if issue.state == "open":
            logging.warning("Issue {} is stil OPEN".format(issue.title))
        else:
            logging.info("Issue ({}:{}) - {} ".format(issue.number,
                                               issue.state, issue.title))
            for comment in issue.get_comments():
                comment_contents.append(comment.body)
    except UnknownObjectException as ue:
        logging.error("Error: Unable to find Issue: {}, {}".format(issue_number, ue))

    return comment_contents


def checkIssueStates(repo, agentid, top):
    agentlabel = repo.get_label(agentid)

    for ix, i in enumerate(
            repo.get_issues(state="open", labels=[agentlabel, ])):
        if int(ix) >= int(top):
            break
        else:
            print("{}) {} [{}] - {}".format(ix, i.number, i.state, i.title))

    for ix, i in enumerate(
            repo.get_issues(state="closed", labels=[agentlabel, ])):
        if int(ix) == int(top):
            break
        else:
            print("{}) {} [{}@{}] - {}".format(ix, i.number, i.state,
                                               i.closed_at, i.title))
