# !/usr/bin/python
# -*- coding: utf-8 -*-

# python lib
import os
import sys
import shutil

# clarisse lib
import ix


def replace_path(path):
    return path.replace("\\", "/")


class _packages:
    "package api"

    @staticmethod
    def get_reference_project(context):
        # p_item = context.get_parent_item()
        # try:
        #     if p_item.attribute_exists("filename"):
        #         filename = p_item.get_attribute('filename').get_string()
        #         if filename.endswith(".project"):
        #             return filename
        #     else:
        #         return get_reference_project(p_item)
        # except:
        #     pass
        p_item = context.get_parent_item()
        if not p_item:
            return

        if p_item.attribute_exists("filename"):
            filename = p_item.get_attribute('filename').get_string()
            if filename.endswith(".project"):
                return {
                    "context": p_item,
                    "old_filename": filename,
                    "is_project": True,
                }

            else:
                return _packages.get_reference_project(p_item)

        else:
            return _packages.get_reference_project(p_item)

    @staticmethod
    def get_all_objects():
        """
        get all objects
        Return:
            object context list
        """
        context = []
        object_list = ix.api.OfObjectArray()
        ix.application.get_factory().get_all_objects("ProjectItem", object_list)

        for count in range(object_list.get_count()):
            context.append(object_list[count])
        return context

    @staticmethod
    def get_attr(context):
        context_list = []
        if context.attribute_exists("filename"):
            filename = context.get_attribute('filename').get_string()
            return {
                "context": context,
                "old_filename": replace_path(filename),
                "is_project": False
            }

    @staticmethod
    def setAttr(data, new_filepath=""):
        context = data.get("context")
        pro = data.get("is_project")
        if not new_filepath:
            new_filepath = data.get("new_filename")

        # if not context.attribute_exists("filename"):
        # return
        if context.get_type() == "FileReferenceContext" and pro == True:
            print("*****" * 10, context)

            ix.cmds.SetReferenceFilename([ix.get_item(str(context))], new_filepath)
            return

        parent_item = context.get_parent_item()
        if parent_item.get_type() == "FileReferenceContext" and pro == False:
            ix.cmds.SetReferenceFilenames(
                [ix.get_item(str(parent_item))], [1, 0], [new_filepath]
            )

        elif parent_item.get_type() != "FileReferenceContext" and pro == False:
            ix.cmds.SetValues(
                [str(context) + ".filename"], [new_filepath]
            )

    @staticmethod
    def dir_structure(project_dir, pro=False):
        """
        目录结构
        """
        project_dir = project_dir.replace("\\", "/")
        resource_path = "{}/{}".format(project_dir, "resource")
        pro_path = "{}/projects".format(resource_path)
        geo_path = "{}/geo".format(resource_path)
        if not os.path.exists(pro_path):
            os.makedirs(pro_path)
        if pro:
            return pro_path

        return geo_path

    @staticmethod
    def remove_duplicate(check_data, key):
        """
        去除重复项
        """
        data_list = []
        if not isinstance(check_data, list):
            raise Exception("data type error!!!")

        for data in check_data:
            if not isinstance(data, dict):
                raise Exception("data type error!!!")

            if not key in data.keys():
                raise Exception("dict not key!!!")

            data_list.append(
                data.get(key)
            )
        return data_list

    @staticmethod
    def deal_with_path(src_dict, dst_path):
        o_folder, o_name = os.path.split(src_dict["old_filename"])
        o_folder, n_name = os.path.split(o_folder)

        new_path = "{}/{}/{}".format(
            dst_path, n_name, o_name
        )
        make_path = "{}/{}".format(
            dst_path, n_name
        )
        return {
            "new_filename": replace_path(new_path),
            "make_path": make_path
        }

    @staticmethod
    def getProjectPath():
        path = ix.application.get_factory().get_vars().get("PDIR").get_string() + "/"
        project_file = ix.application.get_factory().get_vars().get("PNAME").get_string()

        if project_file.find(".project") == -1: project_file += ".project"

        project = path + project_file

        return path, project, project_file


class Package(object):
    def __init__(self):
        pass

    def collect_files(self, dst_path):
        collect = []
        ref_projects = []
        new_collect = []

        dst_project_path = _packages.dir_structure(dst_path, pro=True)
        dst_context_path = _packages.dir_structure(dst_path)
        for context in _packages.get_all_objects():
            old_data_dict = _packages.get_attr(context)  # get context filename attributes
            old_projects_dict = _packages.get_reference_project(context)
            if old_data_dict:
                old_data_dict.update(
                    _packages.deal_with_path(old_data_dict, dst_context_path)
                )
                collect.append(old_data_dict)

            if old_projects_dict:
                old_projects_dict.update(
                    _packages.deal_with_path(old_projects_dict, dst_project_path)
                )
                ref_projects.append(old_projects_dict)

        check_data = []

        def run_collect(collect_data):

            if os.path.exists(collect_data.get("new_filename")):
                if _old_file in check_data:
                    _old_path, _old_name = os.path.split(collect_data.get("new_filename"))
                    base_name, base_text = os.path.splitext(_old_name)
                    _new_path = "{}/{}_{}{}".format(_old_path, base_name, count, base_text)
                    shutil.copy2(collect_data.get("old_filename"), _new_path)
                    _packages.setAttr(collect_data, new_filepath=_new_path)

                else:
                    _packages.setAttr(collect_data)

            else:

                shutil.copy2(collect_data.get("old_filename"), collect_data.get("new_filename"))
                _packages.setAttr(collect_data)

        for count in range(len(collect)):
            data = collect[count]
            if not os.path.exists(data.get("make_path")):
                os.makedirs(data.get("make_path"))

            new_collect.append(data)

            _old_file = data.get("old_filename")

            if not data.get("is_project"):
                run_collect(data)
                check_data.extend(_packages.remove_duplicate(new_collect, "old_filename"))
            else:
                ref_projects.append(data)

        for ref_project in ref_projects:
            new_collect.append(ref_project)
            if ref_project.get("is_project") == True:
                if not os.path.exists(ref_project.get("make_path")):
                    os.makedirs(ref_project.get("make_path"))
                run_collect(ref_project)
                if new_collect:
                    check_data.extend(_packages.remove_duplicate(new_collect, "old_filename"))
        _project = _packages.getProjectPath()
        _new_project_path = "{}/{}".format(dst_path, _project[-1])
        ix.application.save_project(_new_project_path)


if __name__ == "__main__":
    Package().collect_files(r"I:\clarisse_py")