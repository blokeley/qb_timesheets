# Copyright 2013 Tom Oakley
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""qb_timesheets - a translator and plotter for time sheet data from QuickBooks."""

import argparse
from collections import OrderedDict
import csv
import logging
import os
from os.path import join, splitext
import pprint


__version__ = '0.2'


def main():
    args = parse_args()
    
    if args.files:
        process_files(args, *args.files)

    else:
        # Parse CSV files in the current directory
        process_files(args, *(f for f in os.listdir(os.curdir)))


def process_files(args, *files):
    """Process a list of files or directories."""

    for fin in files:
        if os.path.isdir(fin):
            logging.info('Searching ' + fin)
            for root, dirnames, filenames in os.walk(fin):
                for dirnam in dirnames:
                    process_files(args, join(root, dirnam))
                for filename in filenames:
                    process_files(args, join(root, filename))
            continue
            
        # Ignore non-csv files
        if not (fin.endswith('.csv') or fin.endswith('.CSV')):
            logging.info('Ignoring ' + fin)
            continue
        
        logging.info('Processing ' + fin)
        
        with open(fin) as csv_file:
            times = parse_qb(csv_file)
        
        if args.plot or args.save_plot:
            # Create the chart
            plt = create_chart(times)
            
            if args.save_plot:
                # Save the plot to file
                fout = splitext(fin)[0] + '_out.png'
                logging.info('Saving ' + fout)
                plt.savefig(fout)
                
            if args.plot:
                plt.show()
        
        if not args.no_export:
            # Write the CSV file output
            write_csv(fin, times)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--plot', action='store_true', default=False, 
                        help='Plot results in a chart.')
    parser.add_argument('-s', '--save_plot', action='store_true', default=False, 
                        help='Save plot to a file.')
    parser.add_argument('-n', '--no_export', action='store_true', default=False,
                        help='DO NOT export results to a CSV file.')
    parser.add_argument('-v', '--version', action='version', 
                        version='%(prog)s ' + __version__)
    files_help = 'If a directory is given, process the CSV files in that '
    files_help += 'directory. If no files are given, process the files in the '
    files_help += 'current directory.'
    parser.add_argument('files', nargs='*', help=files_help)
    return parser.parse_args()
    

def parse_qb(csv_file):
    """Parse QuickBooks csv_data into a dictionary of project and days."""
    fieldnames = ('a', 'project', 'c', 'Date', 'Name', 
                  'Billing Status', 'Duration')
    reader = csv.DictReader(csv_file, fieldnames)
    
    days = {}
    for row in reader:
        # Use only totals rows
        if row['project'].startswith('Total'):
            # Remove the 'Total ' prefix
            project = row['project'][6:]
            days[project] = float(row['Duration']) / 8
    
    logging.debug(pprint.pformat(days))
    
    # Sort the CSV data into descending order of days
    return OrderedDict(sorted(days.items(), key=lambda t: t[1], reverse=True))

    
def create_chart(hours):
    """Plot a bar chart of time against project."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    
    except ImportError:
        msg = 'Cannot create chart because matplotlib or numpy is not installed.'
        logging.info(msg)
    
    ind = np.arange(len(hours))  # the x locations for the groups
    width = 0.5       # the width of the bars
    
    plt.bar(ind, hours.values(), width)
    plt.xticks(ind + width/2, list(hours.keys()), rotation=90)
    plt.xlabel('Project')
    plt.ylabel('Days booked')
    
    plt.tight_layout()
    return plt


def write_csv(fin, times):
    """Write a CSV file for manual processing."""
    # Create the output filename
    fout = splitext(fin)[0] + '_out.csv'
    logging.info('Writing ' + fout)

    # Write the output CSV file
    with open(fout, 'w') as fout_file:
        writer = csv.writer(fout_file, dialect=csv.unix_dialect)
        writer.writerow(('Project', 'Days'))
        for project, time_ in times.items():
            writer.writerow([project, time_])


if '__main__' == __name__:
    logging.basicConfig(level=logging.INFO)
    main()
