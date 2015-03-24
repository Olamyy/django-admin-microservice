import mailer


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
        self.mailer = kwargs.pop('mailer', mailer)
        self.query = GmailQuery()
        super(GmailQuerySet, self).__init__(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def _clone(self, *args, **kwargs):
        return self

    def count(self):
        return len(self._get_data())

    def __getitem__(self, k):
        return self._get_data()[k]

    def all(self):
        return self._get_data()


class ThreadQuerySet(GmailQuerySet):

    def get(self, *args, **kwargs):
        thread_id = kwargs['id']
        thread = mailer.get_thread_by_id(self.credentials, thread_id)
        thread._meta = self.model._meta
        thread._state = self.model._state
        return thread

    def _get_data(self):
        if not self._cache:
            all_threads = self.mailer.get_all_threads(self.credentials)
            for t in all_threads:
                t._meta = self.model._meta
            self._cache = all_threads
        return self._cache

    def filter(self, *args, **kwargs):
        if len(args) == 0:
            return super(ThreadQuerySet, self).filter(*args, **kwargs)

        q = dict(args[0].children)
        if 'to__icontains' in q:
            all_threads = mailer.get_all_threads(self.credentials, to=q['to__icontains'])
        else:
            all_threads = mailer.get_all_threads(self.credentials)
        for t in all_threads:
            t._meta = self.model._meta

        return ThreadQuerySet(
            all_threads,
            model=self.model,
            credentials=self.credentials,
        )

    #def __iter__(self):
        #try:
            #return iter(self._cache)
        #except AttributeError:
            #pass



class MessageQuerySet(GmailQuerySet):

    def __init__(self, *args, **kwargs):
        self.selected_thread = kwargs.pop('selected_thread', None)
        super(MessageQuerySet, self).__init__(*args, **kwargs)

    def filter(self, *args, **kwargs):
        selected_thread = kwargs.pop('thread', None)
        if selected_thread:
            return MessageQuerySet(
                model=self.model,
                credentials=self.credentials,
                selected_thread=selected_thread
            )
        return self


    def __len__(self):
        return len([k for k in self])

    def __getitem__(self, n):
        return [k for k in self][n]

    def __iter__(self):
        try:
            return iter(self._cache)
        except AttributeError:
            pass

        if not self.selected_thread:
            return super(MessageQuerySet, self).__iter__()

        messages = mailer.get_messages_by_thread_id(
            self.credentials,
            self.selected_thread.id
        )
        for m in messages:
            m._meta = self.model._meta
            m._state = self.model._state
        self._cache = messages
        return iter(messages)

    def get(self, *args, **kwargs):
        message_id = kwargs['pk']
        message = mailer.get_message_by_id(self.credentials, message_id)
        message._meta = self.model._meta
        return message
