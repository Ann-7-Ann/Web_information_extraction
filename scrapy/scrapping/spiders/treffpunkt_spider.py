import scrapy

class Organisations_site1Spider(scrapy.Spider):
    name = 'organisations_site1'
    start_urls = ['https://treffpunkt-ehrenamt.at/alle-organisationen/']

    def parse(self, response):
        # Scrape the list of organization pages (links) from the main page
        max_count = 25
        organizations = response.css('div.singleresult')[:max_count]
        for org in organizations:
            # Extract the link to each organization's page
            detail_page_url = org.css('a.hoverlink::attr(href)').get()
            
            # Follow the link and scrape the organization details
            yield response.follow(detail_page_url, self.parse_organisation)

    def parse_organisation(self, response):
        data = {}
        interesting_info = ['Name: ','Adresse: ', 'Telefon: ','E-Mail: ','Homepage: ','Themenbereich(e) der Organisation:','Ziel der Organisation:']
        # Loop through all <p> tags inside the info container
        details = response.css('div.col-md-5.col-sm-12 p')

        for info in details:
            label = info.css('b::text').get()  # Get the label inside <b>
            if label in interesting_info:
                full_text = ''.join(info.css('::text').getall()).strip()  # Get all text

                if label:
                    value = full_text.replace(label, '').strip()
                    label = label.strip().replace(':', '')
                    data[label] = value

        data['logo'] = response.css('figure img::attr(src)').get()

        yield data

