class GmailQuery(object):
    select_related = False
    order_by = tuple()


class GmailQuerySet(object):
    def using(self, db):
        return self

    def __init__(self, *args, **kwargs):
        self._cache = None
        self.ordered = True
        self.model = kwargs.pop('model')
        self.credentials = kwargs.pop('credentials')
        self.mailer = kwargs.pop('mailer', None)
        self.filter_query = kwargs.pop('filter_query', {})
        self.query = GmailQuery()

    def order_by(self, *args, **kwargs):
        return self

    def none(self, *args, **kwargs):
        cloned_query = self._clone()
        cloned_query.filter_query = {}
        return cloned_query

    def _clone(self, *args, **kwargs):
        return self.__class__(
            model=self.model,
            credentials=self.credentials,
            mailer=self.mailer,
            filter_query=self.filter_query)

    def count(self):
        return len(self._get_data())

    def __getitem__(self, k):
        return self._get_data()[k]

    def __repr__(self):
        from django.utils.encoding import smart_text
        return repr(self._get_data()).encode('utf-8')

    def __iter__(self):
        return iter(self._get_data())

    def all(self):
        return self._get_data()

    def _set_model_attrs(self, instance):
        instance._meta = self.model._meta
        instance._state = self.model._state
        return instance

    def _get_filter_args(self, args, kwargs):
        filter_args = kwargs if kwargs else {}
        if len(args) > 0:
            filter_args.update(dict(args[0].children))
        return filter_args

    def __len__(self):
        return len(self._get_data())


class ThreadQuerySet(GmailQuerySet):
    def get(self, *args, **kwargs):
        filter_args = self._get_filter_args(args, kwargs)
        if 'id' not in filter_args:
            raise Exception("No ID found in Thread GET")

        return ThreadQuerySet(
            model=self.model,
            credentials=self.credentials,
            mailer=self.mailer,
            filter_query={'id': filter_args['id']})[0]

    def _get_data(self):
        """Get the query from the service api.
        register all the possible queries. in this cas
        field_query = ['id', 'to_contains']"""
        if not self._cache:
            messages = self.mailer.get_data(
                self.credentials, self.filter_query, cls=self.model)
            self._cache = [
                self._set_model_attrs(instance) for instance in messages
            ]
            # self._cache = map(self._set_model_attrs, all_threads)
        return self._cache

    def filter(self, *args, **kwargs):
        filter_args = self._get_filter_args(args, kwargs)
        if 'to__icontains' in filter_args:
            return ThreadQuerySet(
                model=self.model,
                credentials=self.credentials,
                mailer=self.mailer,
                filter_query={'to__icontains': filter_args['to__icontains']})
        # import pdb; pdb.set_trace()
        return self


class MessageQuerySet(GmailQuerySet):
    def _create(self, frm, to, message_body, thread_id=None):
        return self.mailer.send_message(
            self.credentials, frm, to, message_body, thread_id=thread_id)

    def filter(self, *args, **kwargs):
        filter_args = self._get_filter_args(args, kwargs)
        if 'thread' in filter_args:

            try:
                tid = filter_args['thread'].id
            except AttributeError:
                tid = filter_args['thread']

            return MessageQuerySet(
                model=self.model,
                credentials=self.credentials,
                mailer=self.mailer,
                filter_query={'thread': tid})
        return self

    def _get_data(self):
        if not self._cache:
            messages = self.mailer.get_data(
                self.credentials, self.filter_query, cls=self.model)
            self._cache = [
                self._set_model_attrs(instance) for instance in messages
            ]
        return self._cache

    def get(self, *args, **kwargs):

        filter_args = self._get_filter_args(args, kwargs)
        if 'pk' not in filter_args:
            raise Exception("No PK found in Message GET")

        return MessageQuerySet(
            model=self.model,
            credentials=self.credentials,
            mailer=self.mailer,
            filter_query={'pk': filter_args['pk']})[0]
