from urlparse import urlparse
from robotparser import RobotFileParser


class RobotsAnalyzer(object):
    def __init__(self):
        self.robots = {}

    def try_add_robot(self, url):
        parsed_url = urlparse(url)
        if parsed_url.netloc not in self.robots:
            try:
                robot_url = parsed_url.scheme + '://' + parsed_url.netloc + \
                            '/robots.txt'
                rp = RobotFileParser(robot_url)
                rp.read()
                self.robots[parsed_url.netloc] = rp
            except IOError as e:
                print str(e)
            except Exception as e:
                print str(e)

    def can_fetch(self, url):
        parsed_url = urlparse(url)
        if parsed_url.netloc in self.robots:
            return self.robots[parsed_url.netloc].can_fetch('*', url)
        else:
            return True
