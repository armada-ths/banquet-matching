import psycopg2
import requests
import json

def connect():
    try:
        conn = psycopg2.connect("dbname='ais_dev' user='ais_dev' host='localhost'")
    except:
        print("Unable to connect to the database")
    return conn.cursor()

# Get all the participant ids for this year's banquet
def get_participants(cur, banquet_id):
    cur.execute("SELECT id \
                FROM banquet_participant \
                WHERE banquet_id = %s \
                EXCEPT \
                SELECT participant_id \
                FROM banquet_invitation \
                WHERE NOT part_of_matching",
                [banquet_id])
    res = cur.fetchall()
    return list(map(lambda x: x[0], res))

# Get all the exhibitor id's for every company representative that attends this year's banquet,
# And something that maps participant ids to exhibitor ids
def get_exhibitors(cur, banquet_id, fair_id):
    cur.execute("SELECT p.id, e.id  \
                FROM banquet_participant p, exhibitors_exhibitor e \
                WHERE p.banquet_id = %s AND NOT p.giveaway AND p.company_id = e.company_id AND e.fair_id = %s",
                (banquet_id, fair_id))
    
    res = cur.fetchall()

    # Create a dictionary that maps a participant id to a company
    participant_to_exhibitor = dict(res)

    # Create a list of all participant id's attending the banquet 
    # (if a company is represented by several people, the different participants will map to the same exhibitor)
    participant_ids = list(map(lambda x: x[0], res))
    return participant_ids, participant_to_exhibitor

# Get a list of the participants that are part of the 
# matching functionality
def get_matching_participants(cur, banquet_id):
    # TODO Verify that all catalogues aren't blank
    cur.execute("SELECT p.id \
                FROM banquet_participant p, banquet_tablematching tm \
                WHERE p.id = tm.participant_id")
    res = cur.fetchall()

    return list(map(lambda x: x[0], res))

# Determine how well every participant matches with every company
def get_matching_results(cur, participant_id):
    info_api_url = 'https://ais.armada.nu/api/matching/choices'
    api_url = 'https://ais.armada.nu/api/matching/'
    
    res = requests.get(info_api_url)
    max_num = json.loads(res.content)['meta']['max_response_size']
    
    
    # Get the students matching data
    cur.execute("SELECT id \
                FROM banquet_tablematching \
                WHERE participant_id = %s", [participant_id])
    
    tm_id = cur.fetchone()[0]

    request_body = {}
    # Get the students matching data for the different categories
    category_to_table_name = {
        "industries": "catalogueindustry",
        "competences": "cataloguecompetence",
        "employments": "catalogueemployment",
        "values": "cataloguevalue",
        "locations": "cataloguelocation"
    }

    weights = {
        "industries": 1,
        "competences": 1,
        "employments": 0,
        "values": 0.25,
        "locations": 0
    }

    for category in ["industries", "competences", "employments", "values", "locations"]:
        request_body[category] = {}
        cur.execute("SELECT " + category_to_table_name[category] + "_id \
                    FROM banquet_tablematching_catalogue_" + category + " \
                    WHERE tablematching_id = %s", [tm_id])
        res = cur.fetchall()
        request_body[category]["answer"] = list(map(lambda x: x[0], res))
        request_body[category]["weight"] = weights[category]
    
    request_body["cities"] = {"answer": "", "weight": 0}
    request_body["response_size"] = max_num

    # Now create the request to the matching api...
    res = requests.post(api_url, headers = {'Content-Type': 'application/json'}, json = request_body)

    # ... and return the relevant response
    data = json.loads(res.content)["similarities"]["total"]
    out = {
        x["exhibitor_id"]: x["similarity"] for x in data
    }
    
    return out

def main():
    CURRENT_FAIR = 4
    CURRENT_BANQUET = 3

    cur = connect()
    participant_list = get_participants(cur, CURRENT_BANQUET)
    company_participant_list, participant_to_exhibitor = get_exhibitors(cur, CURRENT_BANQUET, CURRENT_FAIR)
    matching_student_list = get_matching_participants(cur, CURRENT_BANQUET)
    # The set operations below cause no problem because there are no duplicate participant id's.
    non_matching_student_list = list(set(participant_list) - set(company_participant_list + matching_student_list))
    
    print("Participants to be placed:", len(participant_list))
    print("Company representatives:", len(company_participant_list))
    print("Students subject to matching: ", len(matching_student_list))
    print("Students not subject to matching:", len(non_matching_student_list))

    student_similarities = {}

    for i, student_id in enumerate(matching_student_list):
       print("Fetching data for " + str(i + 1) + "/" + str(len(matching_student_list)) + "...")
       student_similarities[student_id] = get_matching_results(cur, student_id)

    obj = {
       'all_participants': participant_list,
       'matching_students': matching_student_list,
       'non_matching_student': non_matching_student_list,
       'company_participants': company_participant_list,
       'participant_to_exhibitor': participant_to_exhibitor,
       'similarities': student_similarities
    }

    with open('results.json', 'w') as file:
       json.dump(obj, file, indent = 4, separators=(',', ': '))

if __name__ == "__main__":
    main()

