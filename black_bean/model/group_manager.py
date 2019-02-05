from ..util.logger import logged

class GroupManager:

        def __init__(self, arg):
            try:
                self.list = arg["groups"]
            except KeyError:
                self.list = {}

        def __check(self, group_name):
            for group in self.list:
                if group["name"] == group_name:
                    return group
            return None

        @logged(__qualname__)
        def create(self, group_name):
            group={}
            group["name"]=group_name
            group["commands"]=[]
            self.list.append(group)
            return group

        @logged(__qualname__)
        def delete(self, group_name):
            group = self.get(group_name)
            if group:
                self.list.remove(group)
                return True
            return False

        @logged(__qualname__)
        def add(self, group_name, command):
            group = self.get(group_name)
            for cmd in group["commands"]:
                if cmd == command:
                    return False
            group["commands"].append(command)
            return group

        @logged(__qualname__)
        def remove(self, group_name, command):
            group = self.get(group_name)
            try:
                group["commands"].remove(command)
                return group
            except Exception as e:
                return False

        @logged(__qualname__)
        def get(self, group_name):
            group = self.__check(group_name)
            return group

        @logged(__qualname__)
        def get_all(self):
            group_list = self.list
            return group_list
