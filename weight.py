import click
import json
import requests
import os
import datetime as dt
from datetime import datetime
from mllineplot import mllineplot as mlplot
from tabulate import tabulate

CONFIG_PATH = os.path.join(click.get_app_dir('weight'), 'config.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            user_id = config['user_id']
            base_url = config['base_url']
        return user_id, base_url
    else:
        click.echo(f'Config file not found at {CONFIG_PATH}. Please run "weight setup" to set up your configuration.')
        return None, None

@click.group()
def cli():
    pass


@cli.command()
@click.argument('weight', type=float)
@click.argument('date', default=datetime.today().strftime('%Y-%m-%d'), required=False)
def register(weight, date):

    # Read user ID and base URL from config
    user_id, base_url = load_config()

    # Construct JSON data for POST request
    data = {
        'user_id': user_id,
        'weight': weight,
        'date': date,
    }

    # Send POST request to add measurement endpoint
    response = requests.post(f'{base_url}/add_measurement', json=data)

    if response.ok:
        click.echo(f'Registered weight {weight} on {date or "today"}')
    else:
        click.echo(response.text)
        click.echo('Failed to register weight')

@cli.command()
@click.argument('name')
@click.argument('email')
@click.argument('base-url', default='http://localhost:9999')
def setup(name, email, base_url):
    # Send POST request to get user ID
    data = {'name': name, 'email': email}
    response = requests.post(f'{base_url}/get_user_id', json=data)

    if response.ok:
        user_id = response.json()['user_id']
        # Save user ID and base URL to config file
        config = {'user_id': user_id, 'base_url': base_url}
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)
            click.echo(f'Configuration saved to {CONFIG_PATH}.')
    else:
        click.echo('Failed to set up configuration')



@cli.command()
@click.argument('period', default='week', type=click.Choice(['week', 'month', 'all']))
def leaderboard(period):
    # Read user ID and base URL from config
    user_id, base_url = load_config()

    if user_id is not None and base_url is not None:
        # Send GET request to biggest losers endpoint with period parameter
        params = {'user_id': user_id, 'period': period}
        response = requests.get(f'{base_url}/biggest_losers', params=params)

        if response.ok:
            data = response.json()
            # Sort data by weight loss (descending)
            data.sort(key=lambda x: x['weight_loss'], reverse=True)

            # Print period and formatted table
            if period == 'week':
                period_str = 'for the week'
            elif period == 'month':
                period_str = 'for the month'
            else:
                period_str = 'of all time'
            click.echo(f'Leaderboard {period_str}:')
            click.echo(f'{"Name":<10}{"Weight Loss":<10}')
            click.echo(f'{"-----":<10}{"-----------":<10}')
            for row in data:
                name = row['name']
                weight_loss = row['weight_loss']
                if row['user_id'] == user_id:
                    click.echo(click.style(f'{name:<10}{weight_loss:<10.2f}', fg='green'))
                elif weight_loss == data[0]['weight_loss']:
                    click.echo(click.style(f'{name:<10}{weight_loss:<10.2f}', fg='red'))
                else:
                    click.echo(f'{name:<10}{weight_loss:<10.2f}')
        else:
            click.echo('Failed to fetch leaderboard data')

@cli.command()
def plot():
    # Read user ID and base URL from config
    user_id, base_url = load_config()

    if user_id is not None and base_url is not None:
        # Send GET request to get measurements endpoint
        response = requests.get(f'{base_url}/get_measurements/{user_id}')

        if response.ok:
            data = response.json()

            # Extract x and y vectors
            x = []
            y = []
            for i, measurement in enumerate(data):
                date = datetime.fromisoformat(measurement['date'])
                if i == 0:
                    first_date = date
                x.append((date - first_date).days + 1)
                y.append(measurement['weight'])

            # Plot the weight
            mlplot.print_multiline_plot([x], [y])
        else:
            click.echo('Failed to fetch data')

@cli.command()
@click.argument('period', default='week', type=click.Choice(['week', 'month', 'all']))
def list(period):
    # Read user ID and base URL from config
    user_id, base_url = load_config()

    if user_id is not None and base_url is not None:
        # Send GET request to get user measurements endpoint
        params = {'user_id': user_id, 'period': period}
        response = requests.get(f'{base_url}/get_user_measurements', params=params)

        if response.ok:
            data = response.json()

            # Find min and max weight
            min_weight = float('inf')
            max_weight = float('-inf')
            for measurement in data:
                weight = measurement['weight']
                if weight < min_weight:
                    min_weight = weight
                if weight > max_weight:
                    max_weight = weight

            # Format data as table and highlight min and max weights
            headers = ['ID', 'Weight', 'Date']
            table_data = []
            for measurement in data:
                weight = measurement['weight']
                row = [measurement['id'], weight, measurement['date']]
                if weight == min_weight:
                    row[1] = click.style(str(weight), fg='green')
                elif weight == max_weight:
                    row[1] = click.style(str(weight), fg='red')
                table_data.append(row)

            click.echo(tabulate(table_data, headers=headers))
        else:
            click.echo('Failed to fetch data')
    else:
        click.echo('Configuration not found')

@cli.command()
@click.argument('measurement_id', type=int)
@click.argument('new_weight', type=float)
@click.option('--date', default=None)
def edit(measurement_id, new_weight, date=None):
    # Read user ID and base URL from config
    user_id, base_url = load_config()

    if user_id is not None and base_url is not None:
        # Send PUT request to edit measurement endpoint
        endpoint_url = f'{base_url}/edit_measurement/{measurement_id}'
        data = {'weight': new_weight, 'user_id': user_id}
        if date is not None:
            data['date'] = date
        response = requests.put(endpoint_url, json=data)

        if response.ok:
            click.echo(f'Measurement {measurement_id} updated with weight {new_weight}.')
        else:
            click.echo('Failed to update measurement')
    else:
        click.echo('Configuration not found')

@cli.command()
@click.argument('measurement_id', type=int)
def delete(measurement_id):
    # Read user ID and base URL from config
    user_id, base_url = load_config()

    if user_id is not None and base_url is not None:
        # Send DELETE request to delete measurement endpoint
        endpoint_url = f'{base_url}/delete_measurement'
        data = {'measurement_id': measurement_id, 'user_id': user_id}
        response = requests.delete(endpoint_url, json=data)

        if response.ok:
            click.echo(f'Measurement {measurement_id} deleted.')
        else:
            click.echo('Failed to delete measurement.')
    else:
        click.echo('Configuration not found')

from collections import defaultdict
from termcolor import colored

def get_all_userdata(base_url, period):
    url = f"{base_url}/get_all_userdata"
    response = requests.get(url, params={"period": period})
    return response.json()

def format_table(data):
    users = {}
    weights_by_date = defaultdict(dict)

    for user_data in data:
        user_id = user_data['user_id']
        users[user_id] = user_data['name']

        for measurement in user_data['measurements']:
            date = measurement['date']
            weight = measurement['weight']
            weights_by_date[date][user_id] = weight

    headers = ['Date'] + [users[user_id] for user_id in users]
    table_data = []

    # Find the min and max weight for each user
    min_weights = {}
    max_weights = {}
    for user_id in users:
        user_weights = [entry[user_id] for date, entry in weights_by_date.items() if user_id in entry]
        min_weights[user_id] = min(user_weights) if user_weights else None
        max_weights[user_id] = max(user_weights) if user_weights else None

    for date, user_weights in sorted(weights_by_date.items()):
        row = [date]

        for user_id in users:
            weight = user_weights.get(user_id, '')

            if weight:
                if weight == min_weights[user_id]:
                    weight = colored(weight, 'green')
                elif weight == max_weights[user_id]:
                    weight = colored(weight, 'red')

            row.append(weight)

        table_data.append(row)

    return headers, table_data

@cli.command()
@click.argument('period', default='week', type=click.Choice(['week', 'month', 'all']))
def table(period):
    user_id, base_url = load_config()
    data = get_all_userdata(base_url, period)
    headers, table_data = format_table(data)

    print(tabulate(table_data, headers=headers, tablefmt='grid'))

if __name__ == '__main__':
    cli()
