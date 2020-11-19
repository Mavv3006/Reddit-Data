from psaw import PushshiftAPI
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from prawcore.exceptions import NotFound
from praw import Reddit
import datetime
import textwrap
import sys
import os


def filter_dict(data):
    new_dict = {}

    if 'author' in data:
        author_name = "none"
        author_id = "none"
        if data['author'] != None:
            if data['author'].name != None:
                author_name = data['author'].name
            if data['author'].id != None:
                author_id = data['author'].id
        new_dict['author_id'] = author_id
        new_dict['author_name'] = author_name

    if 'id' in data:
        new_dict['_id'] = data['id']
    if 'ups' in data:
        new_dict['upvotes'] = data['ups']
    if 'downs' in data:
        new_dict['downvotes'] = data['downs']
    if 'upvote_ratio' in data:
        new_dict['upvote_ratio'] = data['upvote_ratio']
    if 'over_18' in data:
        new_dict['over_18'] = data['over_18']
    if 'link_flair_text' in data:
        new_dict['link_flair_text'] = data['link_flair_text']

    return new_dict


def add_time_to_dict(data, time):
    data['date'] = time.date().__str__()
    data['time'] = time.time().__str__()
    data['weekday'] = time.weekday()
    return data


def create_collection(db, collection_name):
    if (collection_name not in db.list_collection_names()):
        db.create_collection(collection_name)
    return db[collection_name]


def main():
    reddit = Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGEND')
    )
    print('created Reddit instance')
    api = PushshiftAPI(r=reddit)
    print('created PushshiftAPI instance')
    mongo = MongoClient('database', 27017)
    print('created MongoClient instance')
    subreddit_name = 'de'
    db = mongo['reddit']
    reddit_collection = create_collection(db, subreddit_name)
    start_epoch = int(datetime.datetime(2020, 11, 4).timestamp())
    end_epoch = int(datetime.datetime(2020, 11, 5).timestamp())
    result = api.search_submissions(
        subreddit=subreddit_name, after=start_epoch, before=end_epoch)

    for submission in result:
        if submission is None:
            print("no results")
            exit()

        data = vars(submission)
        id = data['id']

        time = datetime.datetime.utcfromtimestamp(submission.created_utc)

        try:

            data = filter_dict(data)
            data = add_time_to_dict(data, time)

            reddit_collection.insert(data)

            print(f"{ data['date'] } { data['time'] }: { id }")
        except (KeyboardInterrupt, SystemExit):
            raise
        except (TypeError, AttributeError) as e:
            print(e)
            exit()
        except NotFound:
            print("post not found: {}".format(id))
        except DuplicateKeyError:
            print("the document is already in the database")
        except:
            e = sys.exc_info()[0]
            print("error: {}".format(id))
            print()
            print(e)
            exit()

    print()
    print('inserting finished')


if __name__ == "__main__":
    main()
