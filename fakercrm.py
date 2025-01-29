import pandas as pd
from faker import Faker
import random

def generate_crm_data(num_records=100):
    fake = Faker()
    
    data = {
        'phone_number': [],
        'customer_name': [],
        'email': [],
        'last_purchase_date': [],
        'purchase_history': [],
        'customer_segment': [],
        'interaction_history': [],
        'sentiment_history': []
    }
    
    segments = ['Premium', 'Standard', 'Basic']
    
    for _ in range(num_records):
        data['phone_number'].append(fake.phone_number())
        data['customer_name'].append(fake.name())
        data['email'].append(fake.email())
        data['last_purchase_date'].append(fake.date_between(start_date='-1y', end_date='today'))
        data['purchase_history'].append(random.randint(100, 10000))
        data['customer_segment'].append(random.choice(segments))
        data['interaction_history'].append([])  # Empty list for storing call transcriptions
        data['sentiment_history'].append([])    # Empty list for storing sentiment analyses
    
    df = pd.DataFrame(data)
    df.to_excel('crm_data.xlsx', index=False)
    return df

if __name__ == "__main__":
    generate_crm_data()