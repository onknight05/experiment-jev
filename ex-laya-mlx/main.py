import laya_mlx as laya


def old_syntax():
    agent = laya.load("aac6fef/laya-mlx")
    result = agent.predict(
        "I was billed twice. Please refund the duplicate.",
        # "I want to buy a new phone and I have a question about the warranty. Who should I contact?",
        # "I want to buy a new phone and I have a question about billing. Who should I contact?",
        {
            "department": {
                "type": "choice",
                "instructions": "Who should handle this?",
                "criteria": ["billing", "technical", "sales"],
            },
            "urgency": {
                "type": "choice",
                "instructions": "How urgent is this?",
                "criteria": ["low", "medium", "high"],
            },
        },
    )
    answers = result["answers"]
    print(answers)
    # {
    #     "department": {
    #         "type": "choice",
    #         "confidence": 0.627,
    #         "answer_confidence": 0.8893,
    #         "action": { "act_probability": 1.0 },
    #         "choice": "billing",
    #         "probabilities": { "billing": 0.8893, "technical": 0.0835, "sales": 0.0272 }
    #     },
    #     "urgency": {
    #         "type": "choice",
    #         "confidence": 0.0977,
    #         "answer_confidence": 0.5477,
    #         "action": { "act_probability": 1.0 },
    #         "choice": "high",
    #         "probabilities": { "low": 0.1769, "medium": 0.2754, "high": 0.5477 }
    #     }
    # }
    # print(answers["department"]["choice"])
    # print(answers["urgency"]["choice"])

def new_syntax():
    agent = laya.load("aac6fef/laya-mlx")
    result = agent.predict(
        state={"document": "I was billed twice. Please refund the duplicate today."},
        questions={
            "department": {
                "type": "choice",
                "instructions": "Which team should handle this request?",
                "criteria": {
                    "billing": "invoices, payments, refunds",
                    "technical": "bugs and outages",
                    "sales": "new purchases",
                },
            },
            "urgency": {
                "type": "score",
                "instructions": "How urgent is this request?",
                "criteria": ["not urgent", "soon", "critical"],
            },
            "refund": {
                "type": "noul",
                "instructions": "Does the customer ask for money back?",
            },
        },
    )
    answers = result["answers"]
    print(answers)
    # {
    #     "department": {
    #         "type": "choice",
    #         "confidence": 0.8771,
    #         "answer_confidence": 0.9748,
    #         "action": { "act_probability": 1.0 },
    #         "choice": "billing",
    #         "probabilities": { "billing": 0.9748, "technical": 0.014, "sales": 0.0113 }
    #     },
    #     "urgency": {
    #         "type": "score",
    #         "confidence": 0.1024,
    #         "answer_confidence": 0.5648,
    #         "action": { "act_probability": 1.0 },
    #         "score": 0.9871,
    #         "legend": { "0": "not urgent", "1": "soon", "2": "critical" },
    #         "probabilities": { "0": 0.224, "1": 0.5648, "2": 0.2111 }
    #     },
    #     "refund": {
    #         "type": "noul",
    #         "confidence": 0.8489,
    #         "answer_confidence": 0.8489,
    #         "action": { "act_probability": 1.0 },
    #         "noul": 0.8489
    #     }
    # }
    # print(answers["department"]["choice"])
    # print(answers["urgency"]["score"])
    # print(answers["refund"]["noul"])

if __name__ == "__main__":
    # old_syntax()
    new_syntax()