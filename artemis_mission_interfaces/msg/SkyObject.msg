std_msgs/Header header        # stamp = epoch the position was computed for
                              # frame_id = observer / site frame
string name                   # celestial body, e.g. "sun"

# Unit direction from the observer to the body, in the local ENU frame
# (x=East, y=North, z=Up). This is the geometry consumers want directly; the
# angles below are the same direction expressed for human readability.
geometry_msgs/Vector3 direction_enu

float64 azimuth_deg           # deg, north-referenced clockwise (0=N, 90=E), [0, 360)
float64 elevation_deg         # deg, from the local horizontal plane, [-90, 90]
