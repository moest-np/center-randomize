from flask import Flask, redirect, render_template, request, url_for
import csv


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


app = Flask(__name__)


@app.route('/', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/page/<int:page>', methods=['GET', 'POST'])
def home(page):
    school_center_distance_data = []
    with open('../results/school-center-distance.tsv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            school_center_distance_data.append(row)

    form_data = {
        'query': request.args.get('query', ''),
        'scode': request.args.get('scode', ''),
        'cscode': request.args.get('cscode', ''),
        'min_capacity': request.args.get('min_capacity', ''),
        'max_capacity': request.args.get('max_capacity', ''),
        'min_distance': request.args.get('min_distance', ''),
        'max_distance': request.args.get('max_distance', ''),
    }

    filtered_data = [row for row in school_center_distance_data if
                     len(row) >= 10 and
                     (form_data['query'].lower() in row[2].lower() or form_data['query'].lower() in row[6].lower() or form_data['query'].lower() in row[7].lower()) and
                     (form_data['scode'] == '' or row[0] == form_data['scode']) and
                     (form_data['cscode'] == '' or row[5] == form_data['cscode']) and
                     (form_data['min_capacity'] == '' or (row[8].isdigit() and int(row[8]) >= int(form_data['min_capacity']))) and
                     (form_data['max_capacity'] == '' or (row[8].isdigit() and int(row[8]) <= int(form_data['max_capacity']))) and
                     (form_data['min_distance'] == '' or (is_float(row[9]) and float(row[9]) >= float(form_data['min_distance']))) and
                     (form_data['max_distance'] == '' or (is_float(row[9]) and float(row[9]) <= float(form_data['max_distance'])))]

    items_per_page = 10
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_data = filtered_data[start:end]

    return render_template('index.html', data=paginated_data, form_data=form_data, page=page)


@app.route('/reset', methods=['GET'])
def reset():
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
