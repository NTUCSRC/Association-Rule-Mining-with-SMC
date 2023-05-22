import pandas as pd
import random
import sys
from mpyc.runtime import mpc
from imblearn.under_sampling import RandomUnderSampler
import time


async def main():
    secint = mpc.SecInt(16)
    m = len(mpc.parties)
    data_base_path = 'data/clean/heart/'

    if mpc.pid == 0:
        print("You are the first party")

    # read data
    for i in range(m):
        if mpc.pid == i:
            filename = 'heart_part' + str(i+1) + '.csv'
            try:
                df = pd.read_csv(data_base_path + filename)
                df = df.drop(columns=['SleepTime_6_8'])
                y = df['HeartDisease'].to_numpy()
                undersample = RandomUnderSampler(sampling_strategy='majority')
                df, _ = undersample.fit_resample(df, y)
            except:
                print("Error: File not found")
                sys.exit(1)
    print(df.shape)

    await mpc.start()
    start_time = time.time()
    # input min_support and min_confidence
    support = 0
    confidence = 0
    if mpc.pid == 0:
        # support = float(input('Enter min support: '))
        # confidence = float(input('Enter min confidence: '))
        support = float(0.2)
        confidence = float(0.45)

    min_support = await mpc.transfer(support, senders=0)
    min_confidence = await mpc.transfer(confidence, senders=0)

    # calculate total items
    our_records_num = mpc.input(secint(df.shape[0]))
    records_num = sum(our_records_num)
    total_num = await mpc.output(records_num)
    print('Total items:', total_num)

    minimum_support = min_support * total_num

    # get all unique items
    
    unique_items = set(df.columns)

    # sort unique items
    unique_items = sorted(unique_items)
    unique_items = await mpc.transfer(unique_items, senders=0)

    # calculate support
    support_candidate = []
    support_remaining = []
    remain_items = []
    for item in unique_items:
        # Tag: apply smc to get support
        our_items_num = mpc.input(secint(int(df[item].sum())))
        items_num = sum(our_items_num)
        items_num = await mpc.output(items_num)

        if items_num >= minimum_support:
            support_candidate.append([set([item]), items_num])
            support_remaining.append([set([item]), items_num])
            remain_items.append(item)

    # print(support_remaining)
    cnt = 0
    while len(support_candidate) != 0:
        cur_subset = support_candidate.pop(0)[0]
        for item in remain_items:
            if item not in cur_subset:
                new_subset = cur_subset | set([item])
                cnt += 1
                # Tag: apply smc to get support
                our_items_num = mpc.input(secint(int(df[list(new_subset)].all(axis=1).sum())))
                items_num = sum(our_items_num)
                items_num = await mpc.output(items_num)

                # print(str(cnt) + ". " + "new_subset: ", new_subset, "support: ", str(items_num))
                if items_num >= minimum_support:
                    support_candidate.append([new_subset, items_num])
                    support_remaining.append([new_subset, items_num])

    # print(support_remaining)

    # calculate confidence
    # result format: [antecedent, consequent, support, confidence]
    result = []
    for antecedent in support_remaining:
        for consequent in support_remaining:
            antecedent_set, support_antecedent = antecedent[0], antecedent[1]
            consequent_set = consequent[0]

            if antecedent_set.issubset(consequent_set):
                continue
            if consequent_set.issubset(antecedent_set):
                continue
            
            union_set = antecedent_set | consequent_set
            # Tag: apply smc to get support
            # support_union = df[list(union_set)].all(axis=1).sum() / df.shape[0]
            our_items_num = mpc.input(secint(int(df[list(union_set)].all(axis=1).sum())))
            items_num = sum(our_items_num)
            support_union = await mpc.output(items_num)

            if support_union < minimum_support:
                continue
            
            confidence = support_union / support_antecedent
            support_union = support_union / total_num

            if confidence >= min_confidence:
                result.append([antecedent_set, consequent_set, support_union, confidence])

    await mpc.shutdown()

    print("Elapsed Time: ", time.time() - start_time)


    df_result = pd.DataFrame(result, columns=['antecedent', 'consequent', 'support', 'confidence'])

    filename = 'result_part' + str(mpc.pid+1) + '.csv'
    df_result.to_csv(filename, index=False)


mpc.run(main())