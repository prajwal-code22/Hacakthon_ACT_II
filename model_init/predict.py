def predict(query):

    inputs = tokenizer(
        query,
        return_tensors="pt",
        truncation=True,
        max_length=256
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)

    confidence, pred = torch.max(probs, dim=1)

    return pred.item(), confidence.item()