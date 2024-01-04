from sys import stdin
import matplotlib.pyplot as plt
import argparse
import numpy

# this script expects to read from <stdin> BF16 values
# encoded in hexadecimal, e.g.:
# DE00
# BC7A
# 0000
# FEEE
# 3DAF


class IEEEFormat:
    def __init__(self, mantWidth, expWidth, prefixLabel="FP"):
        self.mantWidth = mantWidth
        self.expWidth = expWidth
        self.prefixLabel = prefixLabel

    def parseValue(self, line, post_process=(lambda e, s: (e, s))):
      value = int(line, 16)
      sig = value & (2**self.mantWidth - 1)
      exp = (value >> self.mantWidth) & (2**self.expWidth - 1)
      sign = (value >> (self.mantWidth + self.expWidth)) & 0x1
      bias = - 2**(self.expWidth - 1) + 2
      return [post_process(exp + bias , -sig if  sign else sig)]

    @property
    def name(self):
        return f"{self.prefixLabel}{self.mantWidth + self.expWidth + 1}"


class Discard:
    name = ""

    @staticmethod
    def parseValue(_):
        return []

def parseFmtList(fmtDesc):
    FORMAT_MAP = {
        "FP64": IEEEFormat(52, 11),
        "FP32": IEEEFormat(23, 8),
        "FP16": IEEEFormat(10, 5),
        "BF16": IEEEFormat(7, 8, "BF"),
        "-": Discard
    }
    return [FORMAT_MAP[fmt] for fmt in fmtDesc.split(" ")]


POST_PROCESS_MAP = {
    "id": lambda *v: v,
}

def parse_post_process(post_process_desc):
    return POST_PROCESS_MAP[post_process_desc]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='Random FP value visualizer',
                        description='2D plot of exponent, mantissa values')

    parser.add_argument("format", default=[IEEEFormat(23, 8), Discard, Discard], type=parseFmtList, help="space-separated list of format to parse and plot ('-' to discard field)")

    parser.add_argument('--save',     default=None, help="filename to save the plot", type=str)
    parser.add_argument('--sampling', default=None, help="sample inputs", type=int)
    parser.add_argument('--post-process', default=(lambda e, s: (e, s)), help="", choices=["id", "normalize"], type=parse_post_process)

    args = parser.parse_args()

    def parseLine(line):
        return tuple(sum([fmt.parseValue(value) for fmt, value in zip(args.format, line.split(' '))], []))
            

    inputValueList = [parseLine(line) for line in stdin]


    inputValueList = numpy.array(inputValueList)
    print(f"{len(inputValueList)} value(s) parsed.")
    if args.sampling:
        numSamples = inputValueList.shape[0] if args.sampling is None else args.sampling
        samples = numpy.random.randint(0, inputValueList.shape[0], (numSamples,))
        inputValueList = inputValueList[samples]
        print(f"Sampling {len(inputValueList)} value(s).")


    validFormats = list(filter((lambda v: v != ""), map((lambda fmt: fmt.name), args.format)))
    numPlots = len(validFormats)
    fig, axs = plt.subplots(1, numPlots)

    for (inputValues, ax, fmt) in zip(zip(*inputValueList), axs, validFormats):
        x, y = list(zip(*inputValues))
        scale = 30.0
        ax.scatter(x, y, c="tab:blue", s=scale, label=fmt,
                alpha=0.3, edgecolors='none')

        ax.legend()
        ax.grid(True)

    if args.save is None:
        plt.show()
    else:
       plt.savefig(args.save)
