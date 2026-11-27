import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Important terminology:
# - Recruitment action: The hiring process initiated through an RPA.
# - Certificate: A list of eligible candidates referred to the hiring manager for consideration.
# - Selection: An individual candidate selected from a certificate.
# - Tentative Job Offer (TJO): A preliminary job offer extended to a selected candidate.
# - Entry on Duty (EOD): The date a selected candidate officially begins employment.

# Assumptions
# - Assumes a one-to-one ratios of recruitments to certificates (one recruitment = exactly one certificate)

# THINGS TO CHANGE
# - New vacancies are created with a Poisson distribution, we should get actual historical data
# - The first two iterations of the MC simulation do not really continue from the current state (i.e. 
# it does not account for hires already in the pipline)

def main():
    
    ##### Import and Process Historical Data #####

    # Specify the historical data file
    historical_data_file = "synthetic_federal_hiring_data.csv"
    pay_period_length = 14

    # Process the historical data and retrieve simulation parameters
    historical = process_historical_data(historical_data_file, pay_period_length)

    # Average recruitments per pay period
    average_recruitments_per_pp = historical["average_recruitments_per_pp"]

    # Historical recruitment counts
    recruitments_per_pp = historical["recruitments_per_pp"]

    # Probability a recruitment action results in at least one selection
    selection_rate = historical["selection_rate"]

    # Average number of certificates per recruitment
    certificates_per_recruitment = historical["certificates_per_recruitment"]

    # Average number of selections per certificate
    selections_per_certificate = historical["selections_per_certificate"]
    
    # Array of selections per recruitmnet
    selections_per_recruitment = historical["selections_per_recruitment"]
    
    # Probability a selection results in a hire
    stick_rate = historical["stick_rate"]
    
    # Historical hiring timeline  by pay periods
    historical_timelines_pp = historical["historical_timelines_pp"]
    
    

    ##### Simulation Parameters and Initial Conditions #####

    # Number of authorized positions in the Coast Guard
    total_positions = 10000 ##### ASK FOR THIS NUMBER #######

    # Percentage of authorized positions that are vacant initially
    starting_vacancy_rate = 0.22 ##### ASK FOR THIS NUMBER #######

    # Calculate the initial number of vacant and filled positions
    starting_vacancies = int(total_positions * starting_vacancy_rate)
    starting_filled_positions = total_positions - starting_vacancies

    # Probability that a completed hire is internal
    internal_hire_probability = 0.42 ##### ASK FOR THIS NUMBER #######

    # Number of pay periods between a new vacancy and recruitment process started
    vacancy_to_recruitment_delay = 1 ##### ASK FOR THIS NUMBER #######

    # New vacancy generation
    average_new_vacancies_per_pp = 36

    # Number of pay periods to simulate (two years)
    simulation_periods = 52

    # Number of Monte Carlo simulations
    number_of_simulations = 100

    # Vacancy rates from each simulation
    vacancy_rate_results = np.zeros((number_of_simulations, simulation_periods + 1))



    ##### Monte Carlo Simulation #####

    for simulation in range(number_of_simulations):
        
        print(simulation)
        
        # Initialize number of vacancies
        current_vacancies = starting_vacancies
        vacancy_rate_results[simulation, 0] = (current_vacancies / total_positions)
        
        # Store vacancies waiting for recruitment initiation.
        vacancy_queue = []

        # Store recruitment actions currently in progress.
        recruitment_pipeline = []
        
        for period in range(simulation_periods):

            # Generate new vacancies from employee departures
            new_vacancies = np.random.poisson(average_new_vacancies_per_pp)
            vacancy_queue.append(new_vacancies)

            # New vacancies that are ready to enter recruitment pipeline
            if period + 1 > vacancy_to_recruitment_delay:
                 eligible_vacancies = sum(vacancy_queue[:period + 1 - vacancy_to_recruitment_delay])
            else:
                eligible_vacancies = 0
                
            # Sample the number of recruitments from historical data
            recruitments_created = np.random.choice(recruitments_per_pp)
            
            # Cannot initiate more recruitments than eligible vacancies
            recruitments_created = min(recruitments_created, eligible_vacancies)
            
            # Remove recruited vacancies from the vacancy queue, starting with the oldest
            remaining_recruitments = recruitments_created
            
            # Iterate over vacancy queue
            for i in range(period + 1 - vacancy_to_recruitment_delay):
                
                # Initiate recruitments for eligble vacancies
                vacancies_recruited = min(vacancy_queue[i], remaining_recruitments)
                
                # Subtract initiated recruitments from queue 
                vacancy_queue[i] -= vacancies_recruited
                remaining_recruitments -= vacancies_recruited

                if remaining_recruitments == 0:
                    break

            # Create new recruitment actions
            for i in range(recruitments_created):
                
                # Randomly select a historical recruitment timeline
                eta1= np.random.randint(len(historical_timelines_pp))
                stage_durations = historical_timelines_pp[eta1]
                
                # Create recruitment dictionary
                recruitment = {
                    
                    "period_initiated": period,
                    
                    # Sampled stage durations
                    "rpa_to_cert_duration": stage_durations[0],
                    "cert_to_tjo_duration": stage_durations[1],
                    "tjo_to_eod_duration": stage_durations[2],
                    
                    # Scheduled completion periods
                    "period_certificate": period + stage_durations[0],
                    "period_tjo": None,
                    "period_eod": None,
                    
                    # Hiring outcomes
                    "number_of_selections": 0,
                    "number_of_hires": 0,
                    "internal_hires": 0,
                    "external_hires": 0
                }
                
                # Add to recruitment pipeline
                recruitment_pipeline.append(recruitment)
                
            for recruitment in recruitment_pipeline:
                
                # Generate selections for eligible recruitments                
                if (recruitment["period_certificate"] <= period and recruitment["period_tjo"] is None):
                    
                    # Sample the number of selections from historical data
                    recruitment["number_of_selections"] = np.random.choice(selections_per_recruitment)
                    
                    # Update TJO period
                    recruitment["period_tjo"] = recruitment["period_certificate"] + recruitment["cert_to_tjo_duration"]
                    
                # Generate TJOs for eligible selections
                if (recruitment["period_tjo"] is not None and recruitment["period_tjo"] <= period and recruitment["period_eod"] is None):

                    # Determine number of selections that become hires
                    recruitment["number_of_hires"] = np.random.binomial(recruitment["number_of_selections"],stick_rate)

                    # If there are no hires, close the recruitment 
                    if recruitment["number_of_hires"] == 0:
                        recruitment["period_eod"] = period
                        
                    else:
                        # Update EOD period
                        recruitment["period_eod"] = (recruitment["period_tjo"] + recruitment["tjo_to_eod_duration"])
                        
                # Complete hires that reach EOD
                if (recruitment["period_eod"] is not None and recruitment["period_eod"] <= period):
                    
                    # Cannot hire more people than there are vacancies
                    recruitment["number_of_hires"] = min(recruitment["number_of_hires"], current_vacancies)
                    
                    # Determine number of internal hires
                    recruitment["internal_hires"] = np.random.binomial(recruitment["number_of_hires"], internal_hire_probability)

                    # Calculate number of external hires
                    recruitment["external_hires"] = (recruitment["number_of_hires"] - recruitment["internal_hires"])

                    # Update number of vacancies for external hires
                    current_vacancies -= recruitment["external_hires"]

                    # Add new vacancies to queue for interal hires
                    vacancy_queue[period] += recruitment["internal_hires"]


            remaining_pipeline = []

            for recruitment in recruitment_pipeline:

                # Keep recruitment actions that have not reached EOD
                if (recruitment["period_eod"] is None
                        or recruitment["period_eod"] > period):

                    remaining_pipeline.append(recruitment)

            recruitment_pipeline = remaining_pipeline

            # Calculate vacancy rate
            vacancy_rate_results[simulation, period + 1] = (
                current_vacancies / total_positions
            )


    # ============================================================
    # ANALYZE MONTE CARLO RESULTS
    # ============================================================

    # Calculate average vacancy rate across all simulations.
    average_vacancy_rate = np.mean(vacancy_rate_results, axis=0)

    # Calculate standard deviation across all simulations.
    vacancy_rate_std = np.std(vacancy_rate_results, axis=0)


    # ============================================================
    # PLOT SIMULATION RESULTS
    # ============================================================

    pay_periods = np.arange(simulation_periods + 1)

    plt.figure(figsize=(10, 5))

    plt.plot(
        pay_periods,
        average_vacancy_rate * 100,
        label="Average Vacancy Rate"
    )

    plt.xlabel("Pay Period")
    plt.ylabel("Vacancy Rate (%)")
    plt.title("Projected Organizational Vacancy Rate")
    plt.grid()
    plt.legend()

    plt.show()


##### HISTORICAL DATA PROCESSING FUNCTION #####

def process_historical_data(csv_file, pay_period_length):
    
    # Import historical hiring data
    data = pd.read_csv(csv_file)
    
    # Convert date columns to datetime format
    date_columns = [
        "RPA_Initiated_Date",
        "Cert_Issued_Date",
        "TJO_Accepted_Date",
        "EOD_Date"
    ]

    for column in date_columns:
        data[column] = pd.to_datetime(data[column], errors="coerce")
        
    # Total recruitments from historical data
    total_recruitments = len(data)

    # Determine the date range of the dataset
    start_date = data["RPA_Initiated_Date"].min()
    end_date = data["RPA_Initiated_Date"].max()

    total_days = (end_date - start_date).days + 1
    total_pay_periods = total_days / pay_period_length

    # Calculate  historical average recruitment volume
    average_recruitments_per_pp = total_recruitments / total_pay_periods

    print("\nRECRUITMENT VOLUME")
    print("-----------------------------------")
    print(f"Total recruitments: {total_recruitments}")
    print(f"Average recruitments per pay period: {average_recruitments_per_pp:.2f}")

    ##### Historical Recruitments per Pay Period #####

    recruitments_per_pp = []

    # Total Number of Pay Periods in the Historical Data
    number_of_periods = int(total_days / pay_period_length) + 1

    for period in range(number_of_periods):

        # Determine the start and end dates of the pay period
        period_start = start_date + pd.Timedelta(days=period * 14)
        period_end = period_start + pd.Timedelta(days=14)
        
        # Count recruitments initiated during this pay period
        count = 0

        for date in data["RPA_Initiated_Date"]:

            if date >= period_start and date < period_end:
                count = count + 1

        recruitments_per_pp.append(count)

    # Generate pay-period numbers starting at 1
    pay_period_numbers = range(1, len(recruitments_per_pp) + 1)

    # Plot recruitment volume
    plt.figure(figsize=(10, 5))

    plt.bar(
        pay_period_numbers,
        recruitments_per_pp,
        edgecolor="black"
    )

    plt.xlabel("Pay Period")
    plt.ylabel("Number of Recruitments")
    plt.title("Recruitment Actions per Pay Period")
    plt.grid(axis="y")

    plt.show()


    ##### Historical Hiring Funnel Statistics #####

    # Number of recruitment actions that resulted in at least one candidate being selected
    actions_with_selections = (data["Selections_TJOs"] > 0).sum()

    # Total number of certificates issued across all recruitment actions
    total_certificates = data["Certs_Issued"].sum()

    # Total number of individual candidates selected across all recruitment actions
    total_selections = data["Selections_TJOs"].sum()

    # Total number of candidates who reached their EOD date. This represents the total number of completed hires
    total_hires = data["Hired_EODs"].sum()

    # Percentage of recruitment actions that resulted in at least one candidate being selected
    selection_rate = actions_with_selections / total_recruitments

    # Percentage of individual selections that ultimately resulted in a completed hire
    stick_rate = total_hires / total_selections

    # AVerage number of completed hires per recruitment action
    overall_hiring_rate = total_hires / total_recruitments

    # Average number of certificates issued per recruitment action
    certificates_per_recruitment = total_certificates / total_recruitments

    # Average number of individual selections per certificate
    selections_per_certificate = total_selections / total_certificates
    
    # Number of selections per recruitment action
    selections_per_recruitment = data["Selections_TJOs"].values.tolist()

    # Display the percentage of activity progressing through the different stages of the hiring process.
    print("\nCONVERSION RATES")
    print("-----------------------------------")
    print(f"Recruitment selection rate: {selection_rate:.2%}")
    print(f"Selection-to-hire stick rate: {stick_rate:.2%}")
    print(f"Average hires per recruitment action: {overall_hiring_rate:.2%}")


    ##### Hiring Timelines #####

    # Calculate time between each hiring stage
    data["RPA_to_Cert"] = (data["Cert_Issued_Date"] - data["RPA_Initiated_Date"]).dt.days
    data["Cert_to_TJO"] = (data["TJO_Accepted_Date"] - data["Cert_Issued_Date"]).dt.days
    data["TJO_to_EOD"] = (data["EOD_Date"] - data["TJO_Accepted_Date"]).dt.days

    # Remove missing observations    
    complete_timelines = data.dropna(
        subset=[
            "RPA_to_Cert",
            "Cert_to_TJO",
            "TJO_to_EOD"
        ]
    )
        
    historical_timelines_pp = []
    
    for i in range(len(complete_timelines)):

        # Extract timeline value
        rpa_to_cert = complete_timelines["RPA_to_Cert"].values[i]
        cert_to_tjo = complete_timelines["Cert_to_TJO"].values[i]
        tjo_to_eod = complete_timelines["TJO_to_EOD"].values[i]

        # Convert observed durations into pay periods
        rpa_to_cert = int(np.ceil(rpa_to_cert / pay_period_length))
        cert_to_tjo = int(np.ceil(cert_to_tjo / pay_period_length))
        tjo_to_eod = int(np.ceil(tjo_to_eod / pay_period_length))

        historical_timelines_pp.append([
            rpa_to_cert,
            cert_to_tjo,
            tjo_to_eod
        ])

    historical_results = {

        # Recruitment volume
        "total_recruitments": total_recruitments,
        "average_recruitments_per_pp": average_recruitments_per_pp,
        "recruitments_per_pp": recruitments_per_pp,

        # Hiring funnel
        "total_certificates": total_certificates,
        "total_selections": total_selections,
        "total_hires": total_hires,
        "selection_rate": selection_rate,
        "stick_rate": stick_rate,
        "certificates_per_recruitment": certificates_per_recruitment,
        "selections_per_certificate": selections_per_certificate,
        "selections_per_recruitment": selections_per_recruitment,
        
        # Hiring Funnel Timelines
        "historical_timelines_pp": historical_timelines_pp
    }

    return historical_results

if __name__ == "__main__":
    main()
