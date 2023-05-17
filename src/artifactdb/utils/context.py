from contextvars import ContextVar

# used to set authentication context for each request
auth_user_context:ContextVar[str] = ContextVar("auth-user", default=None)
skip_auth_context:ContextVar[bool] = ContextVar("skip-auth", default=False)

# override default index_name in ElasticManager's default client
es_default_index_context:ContextVar[str] = ContextVar("es-default-indices",default=None)
es_switch_context:ContextVar[str] = ContextVar("es-switch-context",default=None)
switch_context = es_switch_context  # backward compatibility
# override default storage client in StorageManager
storage_default_client_context:ContextVar[str] = ContextVar("storage-default-client",default=None)
storage_switch_context:ContextVar[str] = ContextVar("storage-switch-context",default=None)
# filter sequence clients to matching context name (if any)
# from switch.contexts in config:
# => key in the contexts map
sequence_switch_key:ContextVar[str] = ContextVar("sequence-switch-key",default=None)
# => value in the context map
sequence_context_name:ContextVar[str] = ContextVar("sequence-context-name",default=None)


class ContextException(Exception):
    pass

class ESContext:
    def __init__(self, cfg, context_name):
        self.cfg = cfg
        self.context_name = context_name
        self.ctx_es = None
        self.ctx_switch = None

    def __enter__(self):
        try:
            indices = self.cfg.es.switch.contexts[self.context_name]
            self.ctx_es = es_default_index_context.set(indices)
            self.ctx_switch = es_switch_context.set(self.context_name)
        except KeyError:
            raise ContextException("Context: {} does not exist.".format(self.context_name))

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        es_default_index_context.reset(self.ctx_es)
        es_switch_context.reset(self.ctx_switch)

# backward compatibility
Context = ESContext
