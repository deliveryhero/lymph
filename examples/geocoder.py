import lymph
from geopy.geocoders import GoogleV3


class Geocoder(lymph.Interface):
    def on_start(self):
        self.geolocator = GoogleV3()

    @lymph.rpc()
    def geocode(self, channel, address):
        matched_address, (lat, lng) = self.geolocator.geocode(address)
        channel.reply({
            'address': matched_address,
            'latitude': lat,
            'longitude': lng,
        })
