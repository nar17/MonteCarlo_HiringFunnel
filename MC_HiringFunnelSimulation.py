import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Important terminology:
# - Recruitment action: The hiring process initiated through an RPA.
# - Certificate: A list of eligible candidates referred to the hiring manager for consideration.
# - Selection: An individual candidate selected from a certificate.
# - Tentative Job Offer (TJO): A preliminary job offer extended to a selected candidate.
# - Entry on Duty (EOD): The date a selected candidate officially begins employment.


def main():
    
    ##### Import and Process Historical Data #####

    # Specify the historical data file
    historical_data_file = "synthetic_federal_hiring_data.csv"
    pay_period_length = 14

    # Process the historical data and retrieve simulation parameters
    historical = process_historical_data(
        historical_data_file,
        pay_period_length
    )

    # Average recruitment actions initiated per pay period
    average_recruitments_per_pp = historical["average_recruitments_per_pp"]

    # Historical recruitment counts per pay period
    recruitments_per_pp = historical["recruitments_per_pp"]

    # Probability a recruitment action results in at least one selection
    selection_rate = historical["selection_rate"]

    # Probability an individual selection results in a completed hire
    stick_rate = historical["stick_rate"]

    # Average number of certificates issued per recruitment action
    certificates_per_recruitment = historical["certificates_per_recruitment"]

    # Average number of selections per certificate
    selections_per_certificate = historical["selections_per_certificate"]
    
    

    ##### Simulation Parameters and Initial Conditions #####

    # Number of authorized positions within the Coast Guard
    total_positions = 10000 ##### ASK FOR THIS NUMBER #######

    # Percentage of authorized positions that are vacant initially
    starting_vacancy_rate = 0.22 ##### ASK FOR THIS NUMBER #######

    # Calculate the initial number of vacant and filled positions
    starting_vacancies = int(total_positions * starting_vacancy_rate)
    starting_filled_positions = total_positions - starting_vacancies

    # Probability that a completed hire is internal
    internal_hire_probability = 0.42 ##### ASK FOR THIS NUMBER #######

    # Number of pay periods between vacancy creation and recruitment initiation
    vacancy_to_recruitment_delay = 1 ##### ASK FOR THIS NUMBER #######

    # New vacancy generation
    average_new_vacancies_per_pp = 36

    # Number of pay periods to simulate (two years)
    simulation_periods = 52

    # Number of independent Monte Carlo simulations
    number_of_simulations = 1000

    # Vacancy rates from each simulation
    vacancy_rate_results = np.zeros((number_of_simulations, simulation_periods + 1))



    ##### Monte Carlo Simulation #####

    for simulation in range(number_of_simulations):
        
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

            # 2. Move eligible vacancies into recruitment

            # 3. Progress existing recruitment actions

            # 4. Simulate certificates and candidate selections

            # 5. Simulate accepted TJOs and completed hires

            # 6. Determine internal versus external hires

            # 7. Create replacement vacancies from internal hires

            # 8. Update total vacancies

            # 9. Calculate vacancy rate

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

    # Recruitment-action selection rate:
    # Percentage of recruitment actions that resulted in at least one candidate being selected
    selection_rate = actions_with_selections / total_recruitments

    # Selection-to-hire stick rate:
    # Percentage of individual selections that ultimately resulted in a completed hire
    stick_rate = total_hires / total_selections

    # Overall hiring rate:
    # AVerage number of completed hires per recruitment action
    overall_hiring_rate = total_hires / total_recruitments

    # Average number of certificates issued per recruitment action
    certificates_per_recruitment = total_certificates / total_recruitments

    # Average number of individual selections per certificate
    selections_per_certificate = total_selections / total_certificates

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
    data["RPA_to_EOD"] = (data["EOD_Date"] - data["RPA_Initiated_Date"]).dt.days

    timeline_columns = [
        "RPA_to_Cert",
        "Cert_to_TJO",
        "TJO_to_EOD",
        "RPA_to_EOD"
    ]

    # Convert observed durations into approximate pay periods
    for column in timeline_columns:

        pp_column = column + "_PP"

        data[pp_column] = np.ceil(data[column] / pay_period_length)

    print("\nAVERAGE HIRING TIMELINES (PAY PERIODS)")
    print("-----------------------------------")

    for column in timeline_columns:

        pp_column = column + "_PP"

        print(
            f"{column}: "
            f"{data[pp_column].mean():.2f} pay periods"
        )


    # Plot Hiring Timelines
    plt.figure(figsize=(10, 5))

    plt.hist(
        data["RPA_to_EOD"].dropna(),
        bins=25,
        edgecolor="black"
    )

    plt.xlabel("Total Hiring Time (Days)")
    plt.ylabel("Number of Recruitments")
    plt.title("Distribution of Total Hiring Time")

    plt.grid(axis="y")
    plt.show()

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
    }

    return historical_results

if __name__ == "__main__":
    main()