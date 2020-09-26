''' Default grader script '''
# !! Nothing is allowed to be imported !!
# !! Nothing is allowed to be defined in the global scope apart from the judge function !!
# !! Any aditional functions should be defined inside judge function !!


def judge(input, output, prog_output):
    ''' Script to determine WA/AC '''
    data1 =  output.strip().replace('\n', '')
    data2 =  prog_output.strip().replace('\n', '')

    state = data1 == data2
    if (state):
        msg = 'OK'
    else:
        msg = 'Strings missmatch: ' + data1[0:10] + " (expected) - "+data2[0:10] + " (got)"

    return (state, msg)