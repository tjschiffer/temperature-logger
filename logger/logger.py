from datetime import datetime as datetime
from . import exception
from . import save_to_server
from . import buffer

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def log(values, server_config, exception_config=None):
    """
    Log values to a server, using exception (excluding values
    that have not changed) and buffering (in case the server in unreachable).

    :param values: [
      {
        'sensor_id': (integer),
        'timestamp': (string - format '%Y-%m-%d %H:%M:%S'),
        'value': (float)
      },
      ...
    ]
    :param server_config: {
        'host': (string),
        'user': (string),
        'password': (string),
      }
    :param exception_config: {
        sensor_id (int): compression_value (float)
        ...
      }
    :return: bool
    """
    # Compress the values to ensure they have changed since last reading
    compressed_values = exception.except_values(values, exception_config)
    # Get the values from the buffer
    buffered_values = buffer.read_buffer()

    compressed_and_buffered_values = sorted(compressed_values + buffered_values,
                                            key=lambda k: datetime.strptime(k['timestamp'], DATE_FORMAT))

    # Return success if there are no new values to send to the server (new or buffered)
    if not compressed_and_buffered_values:
        return True

    inserted_rows = save_to_server.save_to_server(compressed_and_buffered_values, server_config)
    if not inserted_rows:
        # If saving to the server completely fails (ex. no internet) save all the values to the buffer
        buffer.write_buffer(compressed_and_buffered_values)
        return False
    else:
        # Clear the buffer since the values are now on the server
        buffer.clear()
        return True
