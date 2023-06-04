import pandas as pd


def filter_categorical(df, column, selected_levels):
    if not selected_levels:
        return df
    return df[df[column].isin(selected_levels)]


def filter_numeric(df, column, lower_bound, upper_bound):
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]


def apply_filters(data, filter_values):
    filtered_data = data.copy()
    print(filter_values)
    print(filter_values.items())
    for column, filter_value in filter_values.items():
        if 'type' in filter_value:
            if filter_value['type'] == 'categorical':
                filtered_data = filtered_data[filtered_data[column].isin(filter_value['values'])]
            else:
                if filter_value['lowerBound']:
                    filtered_data = filtered_data[filtered_data[column] >= filter_value['lowerBound']]
                if filter_value['upperBound']:
                    filtered_data = filtered_data[filtered_data[column] <= filter_value['upperBound']]
        else:
            print(f"Filter value missing 'type' for column '{column}': {filter_value}")

    return filtered_data







