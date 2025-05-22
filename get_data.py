def parse_vehicle_data(soup):
    """
    Parse vehicle data from Facebook Marketplace HTML and return a list of dictionaries.
    Each dictionary contains year, make, model, price, location, mileage, and image URL.
    """
    products = soup.find('div', class_=lambda x: x and 'x1xfsgkm' in x.split())
    
    prices = []
    years = []
    makes = []
    models = []
    locations = []
    mileages = []
    image_urls = []
    listing_urls = []
    
    # Extract prices
    price_elements = products.find_all('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u')
    prices = [price.text.strip() for price in price_elements]
    
    # Extract names and split into year, make, model
    name_elements = products.find_all('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
    names = [name.text.strip() for name in name_elements]
    
    for name in names:
        parts = name.split()
        if len(parts) >= 3:
            years.append(parts[0])
            makes.append(parts[1])
            models.append(' '.join(parts[2:]))
        else:
            # Handle cases where name doesn't split into 3 parts
            years.append('')
            makes.append('')
            models.append('')
    
    # Extract locations and mileages
    location_elements = products.find_all('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft')
    locations_and_miles = [item.text.strip() for item in location_elements]
    
    locations = locations_and_miles[::2]
    raw_miles = locations_and_miles[1::2]
    
    # Process mileages
    for mileage in raw_miles:
        if 'miles' in mileage.lower():
            # Extract numeric part and convert "K" to thousands
            num_part = mileage.split()[0]
            if 'K' in num_part:
                # Remove K and multiply by 1000
                miles = int(float(num_part.replace('K', '')) * 1000)
            else:
                try:
                    miles = int(num_part.replace(',', ''))
                except ValueError:
                    miles = ''
        else:
            miles = ''
        mileages.append(miles)
    
    # Extract image URLs
    image_elements = products.find_all('img', class_='x168nmei x13lgxp2 x5pf9jr xo71vjh xt7dq6l xl1xv1r x6ikm8r x10wlt62 xh8yej3')
    image_urls = [image.attrs['src'] for image in image_elements]
    
    # Extract listing URLs
    url_divs = products.find_all('div', class_="x3ct3a4")
    listing_urls = ['https://www.facebook.com' + url.find('a').get('href') for url in url_divs]
    
    # Determine the minimum length to avoid index errors
    min_length = min(len(prices), len(years), len(makes), len(models), 
                    len(locations), len(mileages), len(image_urls), len(listing_urls))
    
    # Create list of dictionaries
    vehicle_list = []
    for i in range(min_length):
        vehicle = {
            'year': years[i],
            'make': makes[i],
            'model': models[i],
            'price': prices[i],
            'location': locations[i],
            'mileage': mileages[i],
            'image_url': image_urls[i],
            'listing_url': listing_urls[i]
        }
        vehicle_list.append(vehicle)
    
    return vehicle_list
