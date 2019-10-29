# encoding: utf-8

import mock
import json
import pytest
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


class TestDatastoreDump(object):
    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_basic(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"book": "annakarenina"}, {u"book": "warandpeace"}],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get("/datastore/dump/{0}".format(str(resource["id"])))
        assert (
            "_id,book\r\n"
            "1,annakarenina\n"
            "2,warandpeace\n" == response.body
        )

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_all_fields_types(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "fields": [
                {"id": u"b\xfck", "type": "text"},
                {"id": "author", "type": "text"},
                {"id": "published"},
                {"id": u"characters", u"type": u"_text"},
                {"id": "random_letters", "type": "text[]"},
            ],
            "records": [
                {
                    u"b\xfck": "annakarenina",
                    "author": "tolstoy",
                    "published": "2005-03-01",
                    "nested": ["b", {"moo": "moo"}],
                    u"characters": [u"Princess Anna", u"Sergius"],
                    "random_letters": ["a", "e", "x"],
                },
                {
                    u"b\xfck": "warandpeace",
                    "author": "tolstoy",
                    "nested": {"a": "b"},
                    "random_letters": [],
                },
            ],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get("/datastore/dump/{0}".format(str(resource["id"])))
        content = response.body.decode("utf-8")
        expected = (
            u"_id,b\xfck,author,published" u",characters,random_letters,nested"
        )
        assert content[: len(expected)] == expected
        assert "warandpeace" in content
        assert '"[""Princess Anna"",""Sergius""]"' in content

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_alias(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "aliases": "books",
            "records": [{u"book": "annakarenina"}, {u"book": "warandpeace"}],
        }
        helpers.call_action("datastore_create", **data)

        # get with alias instead of id
        response = app.get("/datastore/dump/books")
        assert (
            "_id,book\r\n"
            "1,annakarenina\n"
            "2,warandpeace\n" == response.body
        )

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_does_not_exist_raises_404(self, app):

        app.get("/datastore/dump/does-not-exist", status=404)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_limit(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"book": "annakarenina"}, {u"book": "warandpeace"}],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=1".format(str(resource["id"]))
        )
        content = response.body.decode("utf-8")
        expected_content = u"_id,book\r\n" u"1,annakarenina\n"
        assert content == expected_content

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_q_and_fields(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "fields": [
                {"id": u"b\xfck", "type": "text"},
                {"id": "author", "type": "text"},
                {"id": "published"},
                {"id": u"characters", u"type": u"_text"},
                {"id": "random_letters", "type": "text[]"},
            ],
            "records": [
                {
                    u"b\xfck": "annakarenina",
                    "author": "tolstoy",
                    "published": "2005-03-01",
                    "nested": ["b", {"moo": "moo"}],
                    u"characters": [u"Princess Anna", u"Sergius"],
                    "random_letters": ["a", "e", "x"],
                },
                {
                    u"b\xfck": "warandpeace",
                    "author": "tolstoy",
                    "nested": {"a": "b"},
                    "random_letters": [],
                },
            ],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            u"/datastore/dump/{0}?q=warandpeace&fields=nested,author".format(
                resource["id"]
            )
        )
        content = response.body.decode("utf-8")

        expected_content = u"nested,author\r\n" u'"{""a"": ""b""}",tolstoy\n'
        assert content == expected_content

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_tsv(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "fields": [
                {"id": u"b\xfck", "type": "text"},
                {"id": "author", "type": "text"},
                {"id": "published"},
                {"id": u"characters", u"type": u"_text"},
                {"id": "random_letters", "type": "text[]"},
            ],
            "records": [
                {
                    u"b\xfck": "annakarenina",
                    "author": "tolstoy",
                    "published": "2005-03-01",
                    "nested": ["b", {"moo": "moo"}],
                    u"characters": [u"Princess Anna", u"Sergius"],
                    "random_letters": ["a", "e", "x"],
                },
                {
                    u"b\xfck": "warandpeace",
                    "author": "tolstoy",
                    "nested": {"a": "b"},
                    "random_letters": [],
                },
            ],
        }
        helpers.call_action("datastore_create", **data)

        res = app.get(
            "/datastore/dump/{0}?limit=1&format=tsv".format(
                str(resource["id"])
            )
        )
        content = res.body.decode("utf-8")

        expected_content = (
            u"_id\tb\xfck\tauthor\tpublished\tcharacters\trandom_letters\t"
            u"nested\r\n1\tannakarenina\ttolstoy\t2005-03-01T00:00:00\t"
            u'"[""Princess Anna"",""Sergius""]"\t'
            u'"[""a"",""e"",""x""]"\t"[""b"", '
            u'{""moo"": ""moo""}]"\n'
        )
        assert content == expected_content

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_json(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "fields": [
                {"id": u"b\xfck", "type": "text"},
                {"id": "author", "type": "text"},
                {"id": "published"},
                {"id": u"characters", u"type": u"_text"},
                {"id": "random_letters", "type": "text[]"},
            ],
            "records": [
                {
                    u"b\xfck": "annakarenina",
                    "author": "tolstoy",
                    "published": "2005-03-01",
                    "nested": ["b", {"moo": "moo"}],
                    u"characters": [u"Princess Anna", u"Sergius"],
                    "random_letters": ["a", "e", "x"],
                },
                {
                    u"b\xfck": "warandpeace",
                    "author": "tolstoy",
                    "nested": {"a": "b"},
                    "random_letters": [],
                },
            ],
        }
        helpers.call_action("datastore_create", **data)

        res = app.get(
            "/datastore/dump/{0}?limit=1&format=json".format(
                str(resource["id"])
            )
        )
        content = res.body.decode("utf-8")
        expected_content = (
            u'{\n  "fields": [{"type":"int","id":"_id"},{"type":"text",'
            u'"id":"b\xfck"},{"type":"text","id":"author"},{"type":"timestamp"'
            u',"id":"published"},{"type":"_text","id":"characters"},'
            u'{"type":"_text","id":"random_letters"},{"type":"json",'
            u'"id":"nested"}],\n  "records": [\n    '
            u'[1,"annakarenina","tolstoy","2005-03-01T00:00:00",'
            u'["Princess Anna","Sergius"],["a","e","x"],["b",'
            u'{"moo":"moo"}]]\n]}\n'
        )
        assert content == expected_content

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_xml(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "fields": [
                {"id": u"b\xfck", "type": "text"},
                {"id": "author", "type": "text"},
                {"id": "published"},
                {"id": u"characters", u"type": u"_text"},
                {"id": "random_letters", "type": "text[]"},
            ],
            "records": [
                {
                    u"b\xfck": "annakarenina",
                    "author": "tolstoy",
                    "published": "2005-03-01",
                    "nested": ["b", {"moo": "moo"}],
                    u"characters": [u"Princess Anna", u"Sergius"],
                    "random_letters": ["a", "e", "x"],
                },
                {
                    u"b\xfck": "warandpeace",
                    "author": "tolstoy",
                    "nested": {"a": "b"},
                    "random_letters": [],
                },
            ],
        }
        helpers.call_action("datastore_create", **data)

        res = app.get(
            "/datastore/dump/{0}?limit=1&format=xml".format(
                str(resource["id"])
            )
        )
        content = res.body.decode("utf-8")
        expected_content = (
            u"<data>\n"
            r'<row _id="1">'
            u"<b\xfck>annakarenina</b\xfck>"
            u"<author>tolstoy</author>"
            u"<published>2005-03-01T00:00:00</published>"
            u"<characters>"
            u'<value key="0">Princess Anna</value>'
            u'<value key="1">Sergius</value>'
            u"</characters>"
            u"<random_letters>"
            u'<value key="0">a</value>'
            u'<value key="1">e</value>'
            u'<value key="2">x</value>'
            u"</random_letters>"
            u"<nested>"
            u'<value key="0">b</value>'
            u'<value key="1">'
            u'<value key="moo">moo</value>'
            u"</value>"
            u"</nested>"
            u"</row>\n"
            u"</data>\n"
        )
        assert content == expected_content

    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "3")
    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    def test_dump_with_low_rows_max(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get("/datastore/dump/{0}".format(str(resource["id"])))
        assert get_csv_record_values(response.body) == range(12)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 5)
    def test_dump_pagination(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get("/datastore/dump/{0}".format(str(resource["id"])))
        assert get_csv_record_values(response.body) == range(12)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "7")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 5)
    def test_dump_pagination_csv_with_limit(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=11".format(str(resource["id"]))
        )
        assert get_csv_record_values(response.body) == range(11)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "7")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 6)
    def test_dump_pagination_csv_with_limit_same_as_paginate(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=6".format(str(resource["id"]))
        )
        assert get_csv_record_values(response.body) == range(6)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "6")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 5)
    def test_dump_pagination_with_rows_max(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=7".format(str(resource["id"]))
        )
        assert get_csv_record_values(response.body) == range(7)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "6")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 6)
    def test_dump_pagination_with_rows_max_same_as_paginate(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=7".format(str(resource["id"]))
        )
        assert get_csv_record_values(response.body) == range(7)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "7")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 5)
    def test_dump_pagination_json_with_limit(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=6&format=json".format(
                str(resource["id"])
            )
        )
        assert get_json_record_values(response.body) == range(6)

    @pytest.mark.ckan_config("ckan.plugins", "datastore")
    @pytest.mark.usefixtures("clean_datastore", "with_plugins")
    @pytest.mark.ckan_config("ckan.datastore.search.rows_max", "6")
    @mock.patch("ckanext.datastore.controller.PAGINATE_BY", 5)
    def test_dump_pagination_json_with_rows_max(self, app):
        resource = factories.Resource()
        data = {
            "resource_id": resource["id"],
            "force": True,
            "records": [{u"record": str(num)} for num in range(12)],
        }
        helpers.call_action("datastore_create", **data)

        response = app.get(
            "/datastore/dump/{0}?limit=7&format=json".format(
                str(resource["id"])
            )
        )
        assert get_json_record_values(response.body) == range(7)


def get_csv_record_values(response_body):
    return [int(record.split(",")[1]) for record in response_body.split()[1:]]


def get_json_record_values(response_body):
    return [record[1] for record in json.loads(response_body)["records"]]
