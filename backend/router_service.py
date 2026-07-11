from model_init.initialize_model import initialize_models


class RouterService:

    def __init__(self):

        self.router = initialize_models()

    def predict(self, query: str):

        result = self.router.predict(query)

        return result