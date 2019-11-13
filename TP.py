import random
import json

numberOfTables = 100
numberOfPeoplePerTable = 6
companyOffset = 10000

currentStudent = 0
currentRepresentative = 0
currentNonMatchingStudent = 0

with open('./results.json', 'r') as json_file:
    json_data = json.load(json_file)

allStudentsDict = json_data["similarities"]
studentsNames = json_data["matching_students"]

representativesData = json_data["company_participants"]
random.shuffle(representativesData)
random.shuffle(representativesData)
random.shuffle(representativesData)
representativeCompany = json_data["participant_to_exhibitor"]

nonMatchingStudents = json_data["non_matching_student"]

scoreBanquet = 0
allTables = []


def getNextStudent():
    global currentStudent
    myStudent = ['student', studentsNames[currentStudent]]
    currentStudent += 1
    return myStudent


def getNextRepresentative():
    global currentRepresentative
    myRepresentative = ['representative', representativesData[currentRepresentative],
                        representativeCompany[str(representativesData[currentRepresentative])] + companyOffset]
    currentRepresentative += 1
    return myRepresentative


def getNextNonMatchingStudent():
    global currentNonMatchingStudent
    nonMatchStudent = ['nonmatching_student', nonMatchingStudents[currentNonMatchingStudent]]
    currentNonMatchingStudent += 1
    return nonMatchStudent


def getNumberOfRepresentatives(currTable):
    numberOfRepresentatives = 0
    for spot in currTable:
        if spot[0] == 'representative':
            numberOfRepresentatives += 1
    return numberOfRepresentatives


def getNumberOfStudents(currTable):
    numberOfStudentss = 0
    for spot in currTable:
        if spot[0] == 'student':
            numberOfStudentss += 1
    return numberOfStudentss


def getNextRand(prevRandom, stop):
    newRandom = random.randrange(stop)
    while True:
        if newRandom == prevRandom:
            newRandom = random.randrange(stop)
        else:
            return newRandom


def isCompanyAlreadyAtThatTable(table1, spot1, table2, spot2):
    if spot2[0] == 'representative':
        for spot in table1:
            if spot[0] == 'representative' and spot[2] == spot2[2]:
                return True

    if spot1[0] == 'representative':
        for spot in table2:
            if spot[0] == 'representative' and spot[2] == spot1[2]:
                return True
    return False


def initialPlacement():
    for num in range(numberOfTables):
        allTables.append([])
        for spot in range(numberOfPeoplePerTable):
            if spot % 100 == 1:
                if currentNonMatchingStudent < len(nonMatchingStudents):
                    allTables[num].append(getNextNonMatchingStudent())
                    continue
            # this is here because we want ot avoid the last few tables to only consist of students, because there are more students than representatives
            if len(studentsNames) - currentStudent + 2 > len(representativesData) - currentRepresentative:
                if spot % 3 != 0:
                    if currentStudent < len(studentsNames):
                        allTables[num].append(getNextStudent())
                else:
                    if currentRepresentative < len(representativesData):
                        allTables[num].append(getNextRepresentative())

            else:
                if spot % 2 == 0:
                    if currentStudent < len(studentsNames):
                        allTables[num].append(getNextStudent())
                else:
                    if currentRepresentative < len(representativesData):
                        allTables[num].append(getNextRepresentative())
                    else:
                        if currentStudent < len(studentsNames):
                            allTables[num].append(getNextStudent())


def calculateScores(newAllTables):
    tableNum = 0
    scoreBanquet = 0
    scoresStudents = {}
    scoresTables = []
    for table in newAllTables:
        scoresTables.append(0)
        representativesCount = getNumberOfRepresentatives(table)
        studentsCountPerTable = getNumberOfStudents(table)
        for x in table:
            if x[0] == 'student':
                scoresStudents[x[1]] = 0
                for y in table:
                    if y[0] == 'representative':
                        scoresStudents[x[1]] += allStudentsDict[str(x[1])][str(y[2] - companyOffset)]
                if (representativesCount > 0):
                    scoresStudents[x[1]] /= representativesCount
                scoresTables[tableNum] += scoresStudents[x[1]]
        if (studentsCountPerTable > 0):
            scoresTables[tableNum] /= studentsCountPerTable
        scoreBanquet += scoresTables[tableNum]
        tableNum += 1
    scoreBanquet /= numberOfTables
    return scoreBanquet


initialPlacement()
print("Tables initially: ", allTables)
scoreBanquet = calculateScores(allTables)
print("First score: ", scoreBanquet)

iters = 0
while True:
    randTable1 = random.randrange(numberOfTables)
    randTable2 = getNextRand(randTable1, numberOfTables)
    randSpot1 = random.randrange(numberOfPeoplePerTable)
    randSpot2 = getNextRand(randSpot1, numberOfPeoplePerTable)

    if randSpot1 < len(allTables[randTable1]) and randSpot2 < len(allTables[randTable2]):
        if isCompanyAlreadyAtThatTable(allTables[randTable1], allTables[randTable1][randSpot1], allTables[randTable2],
                                       allTables[randTable2][randSpot2]):
            continue

        swap = allTables[randTable1][randSpot1]
        allTables[randTable1][randSpot1] = allTables[randTable2][randSpot2]
        allTables[randTable2][randSpot2] = swap
    else:
        continue

    if getNumberOfStudents(allTables[randTable1]) > 1 and getNumberOfStudents(
            allTables[randTable2]) > 1 and getNumberOfRepresentatives(
        allTables[randTable1]) > 1 and getNumberOfRepresentatives(
        allTables[randTable1]) < 4 and getNumberOfRepresentatives(
        allTables[randTable2]) > 1 and getNumberOfRepresentatives(allTables[randTable2]) < 4:
        newRes = calculateScores(allTables)
    else:
        allTables[randTable2][randSpot2] = allTables[randTable1][randSpot1]
        allTables[randTable1][randSpot1] = swap
        continue
    if newRes > scoreBanquet:
        scoreBanquet = newRes
        print("Swapped! New score: ", scoreBanquet)
        iters = 0
    else:
        allTables[randTable2][randSpot2] = allTables[randTable1][randSpot1]
        allTables[randTable1][randSpot1] = swap

    iters += 1
    if iters == 60000:
        break

print("Final table placement: ", allTables)
