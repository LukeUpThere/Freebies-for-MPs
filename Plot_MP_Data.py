import matplotlib.pyplot as plt
import pickle
from collections import Counter
import numpy as np

## CLASSES ##
class MP:
    """
    Represent a Member of Parliament with name, constituency, party and 
    donations attributes. Provide methods to add a donation and calculate
    total donations received.
    """
    def __init__(self, name, constituency = 'Unknown', party = 'Unknown'):
        self.name = name
        self.constituency = constituency
        self.party = party
        self.url = ''
        self.donations = []

    def add_donation(self, amount, interest_type, date, hours, text_):
        self.donations.append({"amount": amount,
                               "interest type": interest_type, 
                               "date": date,
                               "hours": hours,
                               "text": text_})

    def total_donations(self):
        total = 0
        for donation in self.donations:
            total += float(donation["amount"])
        return total
    
    def total_hours(self):
        total = 0
        for donation in self.donations:
            if isinstance(donation['hours'], float):
                total += donation['hours']
        return total


## FUNCTIONS ##

def pickle_io(file_name, data = None, save = False, load = False):
    if save and load:
        raise ValueError("Cannot both save and load")
    elif save:
        if data != None:
            with open(f'{file_name}.pydata', 'wb') as f:
                pickle.dump(data, f)
        else:
            raise ValueError("Data cannot be None")
    elif load:
        with open(f'{file_name}.pydata', 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError("Must set save or load to true")

def plot_mp_financial_interests(mps):
    # create empty lists to hold the x and y values and colors for each MP
    x_vals = []
    y_vals = []
    colors = []
    
    # define color map for political parties
    party_color_map = {'Labour': 'red',
                       'Conservative': 'blue', 
                       'Scottish National Party': 'yellow'}
    
    # loop over all MPs
    for mp_name, mp_obj in mps.items():
        # calculate number of interests and total value of financial interests
        num_interests = len(mp_obj.donations)
        total_value = mp_obj.total_donations()
        
        # add x and y values and color for this MP
        x_vals.append(num_interests)
        y_vals.append(total_value)
        colors.append(party_color_map.get(mp_obj.party, 'gray'))
        
        # add label for MPs with total interest exceeding 300,000
        if total_value > 200000 or num_interests > 40 or mp_name == 'Johnson, Boris ':
            plt.annotate(mp_name, xy=(num_interests, total_value), xytext=(num_interests+0.2, total_value+1000))
    
    # create scatter plot
    plt.scatter(x_vals, y_vals, c=colors, marker="X")
    
    # set x and y axis labels
    plt.xlabel('Number of interests')
    plt.ylabel('Total value of financial interests')
    
    # show plot
    plt.show()

def plot_average_donations_by_party(mps):
    # Create dictionary to store total donations and counts for each party
    party_donations = {}
    party_counts = {}
    
    # Loop over MPs and add their donations to the relevant party dictionary entry
    for mp in mps.values():
        party = mp.party
        donations = mp.donations
        total_donations = mp.total_donations()
        if party == 'Labour/Co-operative':
            party = 'Labour'
        if party in party_donations:
            party_donations[party] += total_donations
            party_counts[party] += 1
        else:
            party_donations[party] = total_donations
            party_counts[party] = 1
    
    # Calculate average donation for each party
    party_averages = {party: party_donations[party]/party_counts[party] for party in party_donations}
    
    # Get dominant color for each party logo
    party_colors = {
        'Independent': '#808080',
        'Social Democratic and Labour Party': '#99CC33',
        'Plaid Cymru': '#008142',
        'Scottish National Party': '#FFFF00',
        'DUP': '#D46A4C',
        'Democratic Unionist Party': '#D46A4C',
        'Speaker': '#555555',
        'Alliance': '#F6CB2F',
        'Green': '#6AB023',
        'Alba': '#80AEBD',
        'Liberal Democrats': '#FDBB30',
        'Labour': '#DC241f',
        'Labour/Co-operative': '#DC241f',
        'Sinn Féin': '#008800',
        'Conservative': '#0087DC'
    }
    
    # Create list of party names and average donations in order of appearance in dataset
    party_names = []
    average_donations = []
    for party in party_averages:
        party_names.append(party)
        average_donations.append(party_averages[party])
    
    # Sort data by average donations
    party_names, average_donations = zip(*sorted(zip(party_names, average_donations), key=lambda x: x[1]))
    
    # Create bar chart with coloured bars
    fig, ax = plt.subplots()
    y_pos = np.arange(len(party_names))
    ax.barh(y_pos, average_donations, color=[party_colors[party] for party in party_names])

    for i, v in enumerate(average_donations):
        ax.text(v + 0.5, i, f'{party_names[i]}: £{v:.2f}', color='black')

    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Average Total Donations (£)')
    ax.set_title('Average Total Donations by Party')

    plt.show()

def boxplot_mp_financial_interests(mps):
    # create dictionary to hold total values for each political party
    party_values = {'Labour': [], 'Conservative': [], 'Liberal Democrats': [], 'Scottish National Party': []}
    
    # loop over all MPs
    for mp_name, mp_obj in mps.items():
        if mp_obj.party in party_values:
            # calculate total value of financial interests
            total_value = mp_obj.total_donations()
            
            # add value to list for this MP's political party
            party_values[mp_obj.party].append(total_value)
    
    # create list of lists of values for each political party
    party_data = [party_values['Labour'], party_values['Conservative'], party_values['Liberal Democrats'], party_values['Scottish National Party']]
    
    # create boxplot
    plt.boxplot(party_data, labels=['Labour', 'Conservative', 'Liberal Democrats', 'Scottish National Party'])
    
    # set y-axis label
    plt.ylabel('Total value of financial interests')
    
    # show plot
    plt.show()

## MAIN PROGRAM ##

# Load MPs dictionary
mps = pickle_io('New_MP_Object_Dict', load = True)

boxplot_mp_financial_interests(mps)



# ~ Liberal Democrat
# ~ Independent
# ~ Social Democratic and Labour Party
# ~ Plaid Cymru
# ~ Scottish National Party
# ~ DUP
# ~ Democratic Unionist Party
# ~ Speaker
# ~ Alliance
# ~ Green
# ~ Alba
# ~ Sinn FÃ©in
# ~ Liberal Democrats
# ~ Labour
# ~ Sinn Féin
# ~ Labour/Co-operative
# ~ Conservative
