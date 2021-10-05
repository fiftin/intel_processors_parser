import re

import scrapy
import sqlite3
from processors_parser.spiders.helpers import parse_page


def get_field_value(response, row, field_name):
    value = row.css('.tech-data > *::text').get()
    if field_name == 'name':
        m = re.search(r'/product/details/processors/(\w+)/', response.request.url)
        return value if m is None else m[1] + ' ' + value
    return value


class ProcessorsSpider(scrapy.Spider):
    name = 'intel_processors'
    allowed_domains = ['intel.com']
    start_urls = [
        'https://www.intel.com/content/www/us/en/products/details/processors/core/i3/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/core/i5/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/core/i7/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/core/i9/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/core/x/products.html',

        'https://www.intel.com/content/www/us/en/products/details/processors/celeron/products.html',

        'https://www.intel.com/content/www/us/en/products/details/processors/pentium/gold/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/pentium/silver/products.html',

        'https://www.intel.com/content/www/us/en/products/details/processors/atom/c/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/atom/p/products.html',

        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/scalable/platinum/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/scalable/gold/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/scalable/silver/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/scalable/bronze/products.html',

        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/e/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/w/products.html',
        'https://www.intel.com/content/www/us/en/products/details/processors/xeon/d/products.html',
    ]

    field_labels = {
        'Processor Number': 'name',
        '# of Cores': 'cores',
        '# of Threads': 'threads',
        'Total Threads': 'threads',
        'Launch Date': 'launch_date',
        'Lithography': 'lithography',
        'Processor Base Frequency': 'base_frequency',
        'Configurable TDP-up Frequency': 'base_frequency',
        'Max Turbo Frequency': 'turbo_frequency',
        'Cache': 'cache_size',
        'TDP': 'tdp',
        'Configurable TDP-up': 'tdp',
        'Recommended Customer Price': 'price',
        'Product Collection': 'product_line',
        'Sockets Supported': 'socket',
        'Memory Types': 'memory_type',
        'Vertical Segment': 'vertical_segment',
        'Max Memory Size (dependent on memory type)': 'max_memory_size',
        'Status': 'status',
        'Operating Temperature (Maximum)': 'max_temp'
    }

    field_types = {
        'cores': 'INT',
        'threads': 'INT',
        'name': 'TEXT',
        'launch_date': 'TEXT',
        'lithography': 'INT',
        'base_frequency': 'NUMERIC',
        'turbo_frequency': 'NUMERIC',
        'cache_size': 'NUMERIC',
        'tdp': 'NUMERIC',
        'price': 'NUMERIC',
        'collection': 'TEXT',
        'socket': 'TEXT',
        'memory_type': 'TEXT',
        'url': 'TEXT',
        'vertical_segment': 'TEXT',
        'max_memory_size': 'NUMERIC',
        'max_memory_speed': 'INT'
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        conn = sqlite3.connect('result.db', isolation_level=None)
        c = conn.cursor()

        table_columns = ''
        for field_name, field_type in self.field_types.items():
            table_columns += ', ' + field_name + ' ' + field_type

        c.execute('DROP TABLE IF EXISTS intel_processors')

        c.execute("CREATE TABLE intel_processors("
                  "id INTEGER PRIMARY KEY" +
                  table_columns + ')')

        self.conn = conn

    def parse(self, response, **kwargs):
        if len(response.body) == 0:
            return

        processor_links = response.css('.table-responsive tbody > tr > td:nth-child(2) > a')
        for link in processor_links:
            yield response.follow(link, self.parse_processor)

    def parse_processor(self, response):
        fields = parse_page(
            response.css('.tech-section-row'),
            lambda x: x.css('.tech-label > span::text').get(),
            lambda x, field_name: get_field_value(response, x, field_name),
            self.field_labels,
            self.field_types,
            response.request.url)

        if fields is None:
            return

        c = self.conn.cursor()
        query = 'INSERT INTO intel_processors(' + \
                ', '.join(fields.keys()) + \
                ') VALUES (' + \
                ', '.join(['?' for _ in range(len(fields))]) + \
                ')'
        args = list(fields.values())
        c.execute(query, args)
