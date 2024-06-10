from dateutil.parser import parse as parse_date
import faust
import logging

#Expedia record based on faust.Record
class ExpediaRecord(faust.Record):
    id: int
    date_time: str
    site_name: int
    posa_container: int
    user_location_country: int
    user_location_region: int
    user_location_city: int
    orig_destination_distance: float
    user_id: int
    is_mobile: int
    is_package: int
    channel: int
    srch_ci: str
    srch_co: str
    srch_adults_cnt: int
    srch_children_cnt: int
    srch_rm_cnt: int
    srch_destination_id: int
    srch_destination_type_id: int
    hotel_id: int

#Extended record, for the output topic
class ExpediaExtRecord(ExpediaRecord):
    stay_category: str

#A record, holding only the hotel id and the calculated stay
class ExpediaTestRecord(faust.Record, serializer = 'json'):
    hotel_id: int
    stay_category: str


logger = logging.getLogger(__name__)

#app based on faust.App
app = faust.App('kafkastreams', broker='kafka://kafka:9092')

#topics based on faust.topic
source_topic = app.topic('expedia', value_type=ExpediaRecord)
destination_topic = app.topic('expedia_ext', value_type=ExpediaExtRecord)
test_topic = app.topic('expedia_test', value_type=ExpediaTestRecord)


# The stream-procssing part is decorated with @app.agent, and is async
@app.agent(source_topic, sink=[destination_topic])
async def handle(messages):
    async for message in messages:
        if message is None:
            logger.info('No messages')
            continue

        #Transform your records here

        #Calculate the day difference. On error use -1
        try:
            from_date = parse_date(message.srch_ci)
            to_date = parse_date(message.srch_co)
            diff_days = (to_date - from_date).days
        except Exception as e:
            diff_days = -1

        #convert days to categories
        if diff_days<=0:
            stay_category="Erroneous data"
        elif diff_days<=4:
            stay_category="Short stay"
        elif diff_days<=10:
            stay_category="Standard stay"
        elif diff_days<=14:
            stay_category="Standard extended stay"
        else:
            stay_category="Long stay"

        #return the data to the output topic
        
        # _ext topic
        input_data = message.to_representation()
        
        # _test topic
        test_record = ExpediaTestRecord(
            hotel_id = input_data['hotel_id'],
            stay_category= stay_category
        )

        await test_topic.send(value=test_record.dumps())  # test topic
        yield ExpediaExtRecord(**input_data, stay_category=stay_category) #ext topic


if __name__ == '__main__':
    app.main()
