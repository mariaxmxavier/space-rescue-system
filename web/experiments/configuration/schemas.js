/** Browser editor schema derived from RescueScenario dataclasses. When configuration mounts, these field shapes keep nested inputs aligned with the public API. */
export const scenarioSchema = {
  "type": "object",
  "name": "RescueScenario",
  "fields": [
    {
      "name": "scenario_id",
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "revision",
      "schema": {
        "type": "integer"
      }
    },
    {
      "name": "name",
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "baseline",
      "schema": {
        "type": "object",
        "name": "RunBaseline",
        "fields": [
          {
            "name": "missions",
            "schema": {
              "type": "array",
              "item": {
                "type": "object",
                "name": "Mission",
                "fields": [
                  {
                    "name": "mission_id",
                    "schema": {
                      "type": "string"
                    }
                  },
                  {
                    "name": "station_name",
                    "schema": {
                      "type": "string"
                    }
                  },
                  {
                    "name": "people_count",
                    "schema": {
                      "type": "integer"
                    }
                  },
                  {
                    "name": "created_at",
                    "schema": {
                      "type": "decimal"
                    }
                  },
                  {
                    "name": "requests",
                    "schema": {
                      "type": "array",
                      "item": {
                        "type": "object",
                        "name": "SeatRequest",
                        "fields": [
                          {
                            "name": "request_id",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "command_id",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "mission_id",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "ship_id",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "requested_seats",
                            "schema": {
                              "type": "integer"
                            }
                          },
                          {
                            "name": "confirmed_seats",
                            "schema": {
                              "type": "integer"
                            }
                          },
                          {
                            "name": "outcome",
                            "schema": {
                              "type": "enum",
                              "values": [
                                "pending",
                                "accepted",
                                "partially_accepted",
                                "refused",
                                "cancelled",
                                "expired"
                              ]
                            }
                          },
                          {
                            "name": "submitted_at",
                            "schema": {
                              "type": "decimal"
                            }
                          },
                          {
                            "name": "response_received_at",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "decimal"
                              }
                            },
                            "default": null
                          },
                          {
                            "name": "response_deadline",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "decimal"
                              }
                            },
                            "default": null
                          },
                          {
                            "name": "closed_at",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "decimal"
                              }
                            },
                            "default": null
                          },
                          {
                            "name": "quote_id",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "string"
                              }
                            },
                            "default": null
                          },
                          {
                            "name": "revision_id",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "string"
                              }
                            },
                            "default": null
                          },
                          {
                            "name": "decision_id",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "string"
                              }
                            },
                            "default": null
                          }
                        ]
                      }
                    },
                    "default": []
                  },
                  {
                    "name": "history",
                    "schema": {
                      "type": "array",
                      "item": {
                        "type": "object",
                        "name": "RequestHistoryEntry",
                        "fields": [
                          {
                            "name": "event_id",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "mission_sequence",
                            "schema": {
                              "type": "integer"
                            }
                          },
                          {
                            "name": "recorded_at",
                            "schema": {
                              "type": "decimal"
                            }
                          },
                          {
                            "name": "action",
                            "schema": {
                              "type": "enum",
                              "values": [
                                "request_created",
                                "accepted",
                                "partially_accepted",
                                "refused",
                                "cancelled",
                                "expired"
                              ]
                            }
                          },
                          {
                            "name": "confirmed_seats_delta",
                            "schema": {
                              "type": "integer"
                            }
                          },
                          {
                            "name": "pending_seats_delta",
                            "schema": {
                              "type": "integer"
                            }
                          },
                          {
                            "name": "reason",
                            "schema": {
                              "type": "string"
                            }
                          },
                          {
                            "name": "message_id",
                            "schema": {
                              "type": "optional",
                              "value": {
                                "type": "string"
                              }
                            },
                            "default": null
                          }
                        ]
                      }
                    },
                    "default": []
                  }
                ]
              }
            }
          },
          {
            "name": "market",
            "schema": {
              "type": "object",
              "name": "B3Market",
              "fields": [
                {
                  "name": "market_id",
                  "schema": {
                    "type": "string"
                  }
                },
                {
                  "name": "ships",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "Ship",
                      "fields": [
                        {
                          "name": "ship_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "name",
                          "schema": {
                            "type": "string"
                          }
                        }
                      ]
                    }
                  },
                  "default": []
                },
                {
                  "name": "availabilities",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "ShipAvailability",
                      "fields": [
                        {
                          "name": "availability_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "ship_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "total_seats",
                          "schema": {
                            "type": "integer"
                          }
                        },
                        {
                          "name": "arrival_estimate_seconds",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "available",
                          "schema": {
                            "type": "boolean"
                          }
                        },
                        {
                          "name": "recorded_at",
                          "schema": {
                            "type": "decimal"
                          }
                        }
                      ]
                    }
                  },
                  "default": []
                },
                {
                  "name": "rfqs",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "SeatRFQ",
                      "fields": [
                        {
                          "name": "rfq_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "mission_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "ship_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "availability_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "requested_seats",
                          "schema": {
                            "type": "integer"
                          }
                        },
                        {
                          "name": "status",
                          "schema": {
                            "type": "enum",
                            "values": [
                              "pending",
                              "quoted",
                              "expired"
                            ]
                          }
                        },
                        {
                          "name": "sent_at",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "response_deadline",
                          "schema": {
                            "type": "optional",
                            "value": {
                              "type": "decimal"
                            }
                          },
                          "default": null
                        }
                      ]
                    }
                  },
                  "default": []
                },
                {
                  "name": "quotes",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "RFQOffer",
                      "fields": [
                        {
                          "name": "offer_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "rfq_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "offered_seats",
                          "schema": {
                            "type": "integer"
                          }
                        },
                        {
                          "name": "arrival_estimate_seconds",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "expires_at",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "recorded_at",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "status",
                          "schema": {
                            "type": "enum",
                            "values": [
                              "held",
                              "accepted",
                              "rejected",
                              "expired"
                            ]
                          },
                          "default": "held"
                        },
                        {
                          "name": "request_id",
                          "schema": {
                            "type": "optional",
                            "value": {
                              "type": "string"
                            }
                          },
                          "default": null
                        }
                      ]
                    }
                  },
                  "default": []
                },
                {
                  "name": "offers",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "ShipOffer",
                      "fields": [
                        {
                          "name": "offer_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "mission_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "ship_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "revisions",
                          "schema": {
                            "type": "array",
                            "item": {
                              "type": "object",
                              "name": "ShipOfferRevision",
                              "fields": [
                                {
                                  "name": "revision_id",
                                  "schema": {
                                    "type": "string"
                                  }
                                },
                                {
                                  "name": "revision_number",
                                  "schema": {
                                    "type": "integer"
                                  }
                                },
                                {
                                  "name": "capacity",
                                  "schema": {
                                    "type": "integer"
                                  }
                                },
                                {
                                  "name": "arrival_estimate_seconds",
                                  "schema": {
                                    "type": "decimal"
                                  }
                                },
                                {
                                  "name": "available",
                                  "schema": {
                                    "type": "boolean"
                                  }
                                },
                                {
                                  "name": "recorded_at",
                                  "schema": {
                                    "type": "decimal"
                                  }
                                }
                              ]
                            }
                          }
                        }
                      ]
                    }
                  },
                  "default": []
                },
                {
                  "name": "quote_history",
                  "schema": {
                    "type": "array",
                    "item": {
                      "type": "object",
                      "name": "QuoteStatusChange",
                      "fields": [
                        {
                          "name": "quote_id",
                          "schema": {
                            "type": "string"
                          }
                        },
                        {
                          "name": "status",
                          "schema": {
                            "type": "enum",
                            "values": [
                              "held",
                              "accepted",
                              "rejected",
                              "expired"
                            ]
                          }
                        },
                        {
                          "name": "changed_at",
                          "schema": {
                            "type": "decimal"
                          }
                        },
                        {
                          "name": "request_id",
                          "schema": {
                            "type": "optional",
                            "value": {
                              "type": "string"
                            }
                          },
                          "default": null
                        }
                      ]
                    }
                  },
                  "default": []
                }
              ]
            }
          },
          {
            "name": "command_index",
            "schema": {
              "type": "array",
              "item": {
                "type": "value"
              }
            },
            "default": []
          },
          {
            "name": "message_index",
            "schema": {
              "type": "array",
              "item": {
                "type": "value"
              }
            },
            "default": []
          },
          {
            "name": "delivery_index",
            "schema": {
              "type": "array",
              "item": {
                "type": "value"
              }
            },
            "default": []
          },
          {
            "name": "decision_index",
            "schema": {
              "type": "array",
              "item": {
                "type": "value"
              }
            },
            "default": []
          },
          {
            "name": "session_index",
            "schema": {
              "type": "array",
              "item": {
                "type": "value"
              }
            },
            "default": []
          }
        ]
      }
    },
    {
      "name": "response_rules",
      "schema": {
        "type": "array",
        "item": {
          "type": "object",
          "name": "ScriptedResponse",
          "fields": [
            {
              "name": "ship_id",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "request_ordinal",
              "schema": {
                "type": "integer"
              }
            },
            {
              "name": "outcome",
              "schema": {
                "type": "enum", "values": ["accepted", "partially_accepted", "refused"]
              }
            },
            {
              "name": "confirmed_seats",
              "schema": {
                "type": "optional",
                "value": {
                  "type": "integer"
                }
              },
              "default": null
            }
          ]
        }
      }
    },
    {
      "name": "availability_changes",
      "schema": {
        "type": "array",
        "item": {
          "type": "object",
          "name": "ShipAvailability",
          "fields": [
            {
              "name": "availability_id",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "ship_id",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "total_seats",
              "schema": {
                "type": "integer"
              }
            },
            {
              "name": "arrival_estimate_seconds",
              "schema": {
                "type": "decimal"
              }
            },
            {
              "name": "available",
              "schema": {
                "type": "boolean"
              }
            },
            {
              "name": "recorded_at",
              "schema": {
                "type": "decimal"
              }
            }
          ]
        }
      }
    },
    {
      "name": "time_horizon_seconds",
      "schema": {
        "type": "decimal"
      }
    },
    {
      "name": "seed",
      "schema": {
        "type": "integer"
      }
    },
    {
      "name": "event_budget",
      "schema": {
        "type": "integer"
      }
    },
    {
      "name": "communication_profiles",
      "schema": {
        "type": "array",
        "item": {
          "type": "object",
          "name": "CommunicationProfile",
          "fields": [
            {
              "name": "profile_id",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "ship_id",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "outbound_delay_seconds",
              "schema": {
                "type": "decimal"
              }
            },
            {
              "name": "decision_delay_seconds",
              "schema": {
                "type": "decimal"
              }
            },
            {
              "name": "return_delay_seconds",
              "schema": {
                "type": "decimal"
              }
            },
            {
              "name": "loss_rule",
              "schema": {
                "type": "array",
                "item": {
                  "type": "integer"
                }
              },
              "default": []
            },
            {
              "name": "duplication_rule",
              "schema": {
                "type": "array",
                "item": {
                  "type": "integer"
                }
              },
              "default": []
            },
            {
              "name": "reordering_rule",
              "schema": {
                "type": "array",
                "item": {
                  "type": "integer"
                }
              },
              "default": []
            }
          ]
        }
      },
      "default": []
    }
  ]
};
