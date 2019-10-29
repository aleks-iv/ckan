# encoding: utf-8
"""
NB Don't test logic functions here. This is just for the mechanics of the API
controller itself.
"""
import json
import re

import __builtin__ as builtins

import mock
import pytest

from pyfakefs import fake_filesystem

from ckan.lib.helpers import url_for
import ckan.tests.helpers as helpers
from ckan.tests import factories
from ckan.lib import uploader as ckan_uploader

fs = fake_filesystem.FakeFilesystem()
fake_os = fake_filesystem.FakeOsModule(fs)
fake_open = fake_filesystem.FakeFileOpen(fs)
real_open = open


def mock_open_if_open_fails(*args, **kwargs):
    try:
        return real_open(*args, **kwargs)
    except (OSError, IOError):
        return fake_open(*args, **kwargs)


class TestApiController(object):
    @pytest.mark.usefixtures("clean_db")
    @pytest.mark.ckan_config("ckan.storage_path", "/doesnt_exist")
    @mock.patch.object(builtins, "open", side_effect=mock_open_if_open_fails)
    @mock.patch.object(ckan_uploader, "os", fake_os)
    @mock.patch.object(ckan_uploader, "_storage_path", new="/doesnt_exist")
    def test_resource_create_upload_file(self, _, app):
        user = factories.User()
        pkg = factories.Dataset(creator_user_id=user["id"])
        # upload_content = StringIO()
        # upload_content.write('test-content')

        url = url_for(
            controller="api",
            action="action",
            logic_function="resource_create",
            ver="/3",
        )
        env = {"REMOTE_USER": user["name"].encode("ascii")}
        postparams = {"name": "test-flask-upload", "package_id": pkg["id"]}
        upload_content = "test-content"
        upload_info = ("upload", "test-upload.txt", upload_content)

        resp = app.post(
            url,
            params=postparams,
            upload_files=[upload_info],
            extra_environ=env
            # content_type= 'application/json'
        )
        result = resp.json["result"]
        assert "upload" == result["url_type"]
        assert len(upload_content) == result["size"]

    @pytest.mark.usefixtures("clean_db")
    def test_unicode_in_error_message_works_ok(self, app):
        # Use tag_delete to echo back some unicode

        org_url = "/api/action/tag_delete"
        data_dict = {"id": u"Delta symbol: \u0394"}  # unicode gets rec'd ok
        postparams = "%s=1" % json.dumps(data_dict)
        response = app.post(url=org_url, params=postparams, status=404)
        # The unicode is backslash encoded (because that is the default when
        # you do str(exception) )
        assert "Delta symbol: \\u0394" in response.body

    @pytest.mark.usefixtures("clean_db", "clean_index")
    def test_dataset_autocomplete_name(self, app):
        dataset = factories.Dataset(name="rivers")
        url = url_for(
            controller="api", action="dataset_autocomplete", ver="/2"
        )
        assert url == "/api/2/util/dataset/autocomplete"

        response = app.get(url=url, params={"incomplete": u"rive"}, status=200)

        results = json.loads(response.body)
        assert results == {
            u"ResultSet": {
                u"Result": [
                    {
                        u"match_field": u"name",
                        u"name": u"rivers",
                        u"match_displayed": u"rivers",
                        u"title": dataset["title"],
                    }
                ]
            }
        }
        assert (
            response.headers["Content-Type"]
            == "application/json;charset=utf-8"
        )

    @pytest.mark.usefixtures("clean_db", "clean_index")
    def test_dataset_autocomplete_title(self, app):
        dataset = factories.Dataset(name="test_ri", title="Rivers")
        url = url_for(
            controller="api", action="dataset_autocomplete", ver="/2"
        )
        assert url == "/api/2/util/dataset/autocomplete"

        response = app.get(url=url, params={"incomplete": u"riv"}, status=200)

        results = json.loads(response.body)
        assert results == {
            u"ResultSet": {
                u"Result": [
                    {
                        u"match_field": u"title",
                        u"name": dataset["name"],
                        u"match_displayed": u"Rivers (test_ri)",
                        u"title": u"Rivers",
                    }
                ]
            }
        }
        assert (
            response.headers["Content-Type"]
            == "application/json;charset=utf-8"
        )

    @pytest.mark.usefixtures("clean_db")
    def test_tag_autocomplete(self, app):
        factories.Dataset(tags=[{"name": "rivers"}])
        url = url_for(controller="api", action="tag_autocomplete", ver="/2")
        assert url == "/api/2/util/tag/autocomplete"

        response = app.get(url=url, params={"incomplete": u"rive"}, status=200)

        results = json.loads(response.body)
        assert results == {"ResultSet": {"Result": [{"Name": "rivers"}]}}
        assert (
            response.headers["Content-Type"]
            == "application/json;charset=utf-8"
        )

    @pytest.mark.usefixtures("clean_db")
    def test_group_autocomplete_by_name(self, app):
        org = factories.Group(name="rivers", title="Bridges")
        url = url_for(controller="api", action="group_autocomplete", ver="/2")
        assert url == "/api/2/util/group/autocomplete"

        response = app.get(url=url, params={"q": u"rive"}, status=200)

        results = json.loads(response.body)
        assert len(results) == 1
        assert results[0]["name"] == "rivers"
        assert results[0]["title"] == "Bridges"
        assert (
            response.headers["Content-Type"]
            == "application/json;charset=utf-8"
        )

    @pytest.mark.usefixtures("clean_db")
    def test_group_autocomplete_by_title(self, app):
        org = factories.Group(name="frogs", title="Bugs")
        url = url_for(controller="api", action="group_autocomplete", ver="/2")

        response = app.get(url=url, params={"q": u"bug"}, status=200)

        results = json.loads(response.body)
        assert len(results) == 1
        assert results[0]["name"] == "frogs"

    @pytest.mark.usefixtures("clean_db")
    def test_organization_autocomplete_by_name(self, app):
        org = factories.Organization(name="simple-dummy-org")
        url = url_for(
            controller="api", action="organization_autocomplete", ver="/2"
        )
        assert url == "/api/2/util/organization/autocomplete"

        response = app.get(url=url, params={"q": u"simple"}, status=200)

        results = json.loads(response.body)
        assert len(results) == 1
        assert results[0]["name"] == "simple-dummy-org"
        assert results[0]["title"] == org["title"]
        assert (
            response.headers["Content-Type"]
            == "application/json;charset=utf-8"
        )

    @pytest.mark.usefixtures("clean_db")
    def test_organization_autocomplete_by_title(self, app):
        org = factories.Organization(title="Simple dummy org")
        url = url_for(
            controller="api", action="organization_autocomplete", ver="/2"
        )

        response = app.get(url=url, params={"q": u"simple dum"}, status=200)

        results = json.loads(response.body)
        assert len(results) == 1
        assert results[0]["title"] == "Simple dummy org"

    @pytest.mark.usefixtures("clean_db")
    def test_config_option_list_access_sysadmin(self, app):
        user = factories.Sysadmin()
        url = url_for(
            controller="api",
            action="action",
            logic_function="config_option_list",
            ver="/3",
        )

        app.get(
            url=url,
            params={},
            extra_environ={"REMOTE_USER": user["name"].encode("ascii")},
            status=200,
        )

    @pytest.mark.usefixtures("clean_db")
    def test_config_option_list_access_sysadmin_jsonp(self, app):
        user = factories.Sysadmin()
        url = url_for(
            controller="api",
            action="action",
            logic_function="config_option_list",
            ver="/3",
        )

        app.get(
            url=url,
            params={"callback": "myfn"},
            extra_environ={"REMOTE_USER": user["name"].encode("ascii")},
            status=403,
        )

    @pytest.mark.usefixtures("clean_db")
    def test_jsonp_works_on_get_requests(self, app):

        dataset1 = factories.Dataset()
        dataset2 = factories.Dataset()

        url = url_for(
            controller="api",
            action="action",
            logic_function="package_list",
            ver="/3",
        )

        res = app.get(url=url, params={"callback": "my_callback"})
        assert re.match(r"my_callback\(.*\);", res.body), res
        # Unwrap JSONP callback (we want to look at the data).
        start = len("my_callback") + 1
        msg = res.body[start: -2]
        res_dict = json.loads(msg)
        assert res_dict["success"]
        assert sorted(res_dict["result"]) == sorted(
            [dataset1["name"], dataset2["name"]]
        )

    @pytest.mark.usefixtures("clean_db")
    def test_jsonp_returns_javascript_content_type(self, app):
        url = url_for(
            controller="api",
            action="action",
            logic_function="status_show",
            ver="/3",
        )

        res = app.get(url=url, params={"callback": "my_callback"})
        assert "application/javascript" in res.headers.get("Content-Type")

    @pytest.mark.usefixtures("clean_db")
    def test_jsonp_does_not_work_on_post_requests(self, app):

        dataset1 = factories.Dataset()
        dataset2 = factories.Dataset()

        url = url_for(
            controller="api",
            action="action",
            logic_function="package_list",
            ver="/3",
            callback="my_callback",
        )

        res = app.post(url=url)
        # The callback param is ignored and the normal response is returned
        assert not res.body.startswith("my_callback")
        res_dict = json.loads(res.body)
        assert res_dict["success"]
        assert sorted(res_dict["result"]) == sorted(
            [dataset1["name"], dataset2["name"]]
        )
